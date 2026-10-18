"""Utilidades de bajo consumo de memoria para los baselines B0 y B1.

Las tablas de estados son demasiado grandes para cargar el corpus completo en la
RAM de Colab. ``ScenarioStream`` lee un día por vez, aplica el mismo filtro
``usable`` que ``load_scenario`` y conserva las particiones por ``game_id``.
"""

from dataclasses import dataclass
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.special import expit, logit

from ptcg_wp.features import usable
from ptcg_wp.splits import assign_stage


REQUIRED_COLUMNS = ("game_id", "turn", "setup", "decided", "y")


@dataclass
class ScenarioStream:
    """Itera las filas útiles de un escenario, un archivo diario por vez."""

    data_dir: Path
    scenario: str
    columns: tuple[str, ...]
    batch_size: int = 32768

    def __post_init__(self):
        self.data_dir = Path(self.data_dir)
        if self.batch_size < 1:
            raise ValueError("batch_size debe ser positivo")
        part = pd.read_parquet(self.data_dir / "particiones.parquet",
                               columns=["game_id", f"split_{self.scenario}"])
        self._splits = part.set_index("game_id")[f"split_{self.scenario}"]
        self._columns = tuple(dict.fromkeys((*self.columns, *REQUIRED_COLUMNS)))
        self.cuts = self._stage_cuts()

    @property
    def files(self):
        return sorted(self.data_dir.glob("estados_*.parquet"))

    def _read_batches(self, columns):
        """Libera el lector entre grupos Parquet para no retener el archivo entero."""
        for path in self.files:
            with pq.ParquetFile(path) as parquet:
                for group in range(parquet.num_row_groups):
                    records = parquet.iter_batches(batch_size=self.batch_size, columns=columns,
                                                   row_groups=[group], use_threads=False)
                    try:
                        for record in records:
                            frame = record.to_pandas(use_threads=False, split_blocks=True)
                            yield frame
                            del frame, record
                    finally:
                        # El lector puede retener buffers de grupos ya recorridos.
                        # Reiniciarlo limita esa retención a un grupo Parquet.
                        del records
                        pa.default_memory_pool().release_unused()

    def _stage_cuts(self):
        # Frecuencias de turnos: reproduce los cuantiles lineales sin guardar cada fila.
        counts = Counter()
        cols = ["game_id", "turn", "setup", "decided"]
        for frame in self._read_batches(cols):
            part = usable(frame)
            turns = part.loc[part["game_id"].map(self._splits).eq("train"), "turn"]
            if not np.isfinite(turns).all():
                raise ValueError("turn contiene valores no finitos en train")
            counts.update(turns.value_counts().to_dict())
        if not counts:
            raise ValueError("no hay estados útiles en train")
        values = np.array(sorted(counts))
        cumulative = np.cumsum([counts[value] for value in values])
        cuts = []
        for q in (1 / 3, 2 / 3):
            rank = (cumulative[-1] - 1) * q
            low, high = np.floor(rank), np.ceil(rank)
            a, b = values[np.searchsorted(cumulative, [low, high], side="right")]
            cuts.append(float(a + (b - a) * (rank - low)))
        return tuple(cuts)

    def iter_batches(self, split_name, selected_games=None, columns=None):
        """Lee lotes acotados; una partida puede atravesar varios lotes.

        Los pesos deben usar conteos de la partición completa, nunca del lote.
        B0/B1 conservan su iterador diario por compatibilidad.
        """
        if split_name not in ("train", "val"):
            raise ValueError("este flujo de desarrollo solo admite train y val")
        cols = list(dict.fromkeys((*self._columns, *REQUIRED_COLUMNS))) if columns is None else list(
            dict.fromkeys((*columns, *REQUIRED_COLUMNS))
        )
        selected = None if selected_games is None else pd.Index(selected_games)
        for frame in self._read_batches(cols):
            part = usable(frame)
            split = part["game_id"].map(self._splits)
            if split.isna().any():
                raise ValueError("hay filas útiles sin partición")
            keep = split.eq(split_name)
            if selected is not None:
                keep &= part["game_id"].isin(selected)
            part = part.loc[keep].copy()
            if part.empty:
                continue
            part["split"] = split_name
            part["stage"] = assign_stage(part["turn"].to_numpy(), self.cuts)
            yield part

    def __iter__(self):
        for path in self.files:
            day = usable(pd.read_parquet(path, columns=list(self._columns)))
            split = day["game_id"].map(self._splits)
            if split.isna().any():
                raise ValueError("hay filas útiles sin partición")
            # B0 y B1 solo usan train para ajustar y val para medir.
            keep = split.isin(["train", "val"])
            day = day.loc[keep].copy()
            split = split.loc[keep]
            day["split"] = split.to_numpy()
            day["stage"] = assign_stage(day["turn"].to_numpy(), self.cuts)
            yield day


def weights_by_game(game_ids):
    """Peso 1/n por fila, para que cada partida sume exactamente uno."""
    ids = pd.Series(game_ids, copy=False)
    return ids.map(ids.value_counts(sort=False)).rdiv(1.0).to_numpy(dtype=float)


def b1_score(frame, hp_unit):
    """Puntuación fija de recursos propuesta para B1."""
    prize_advantage = frame["opp_prizes"] - frame["own_prizes"]
    return (prize_advantage + frame["diff_total_hp"] / hp_unit + frame["diff_bench_n"]).to_numpy(float)


def b0_and_hp_unit(stream):
    """Calcula B0 y la unidad de PV de B1 usando solo los días de train."""
    game_win_share = []
    hp_sum = 0.0
    hp_weight = 0.0
    for day in stream:
        train = day.loc[day["split"] == "train"]
        by_game = train.groupby("game_id", sort=False)["y"].agg(["sum", "count"])
        game_win_share.append((by_game["sum"] / by_game["count"]).to_numpy())

        w = weights_by_game(train["game_id"])
        hp = np.concatenate((train["own_active_max_hp"].to_numpy(),
                             train["opp_active_max_hp"].to_numpy()))
        hp_w = np.concatenate((w, w))
        valid = hp > 0
        hp_sum += np.dot(hp[valid], hp_w[valid])
        hp_weight += hp_w[valid].sum()
    return float(np.concatenate(game_win_share).mean()), float(hp_sum / hp_weight)


def fit_b1_mapping(stream, hp_unit, base_probability, max_iter=6, tolerance=1e-8):
    """Ajusta la sigmoide de B1 por Newton-Raphson, sin guardar train completo.

    Es la misma regresión logística de una variable que se usaba en el cuaderno,
    calculada por días para no agotar la RAM.
    """
    beta = np.array([logit(np.clip(base_probability, 1e-8, 1 - 1e-8)), 0.0])
    for _ in range(max_iter):
        gradient = np.zeros(2)
        hessian = np.zeros((2, 2))
        for day in stream:
            train = day.loc[day["split"] == "train"]
            score = b1_score(train, hp_unit)
            y = train["y"].to_numpy(float)
            w = weights_by_game(train["game_id"])
            probability = expit(beta[0] + beta[1] * score)
            residual = w * (y - probability)
            gradient += (residual.sum(), np.dot(residual, score))
            curvature = w * probability * (1 - probability)
            hessian += ((curvature.sum(), np.dot(curvature, score)),
                        (np.dot(curvature, score), np.dot(curvature, score * score)))
        step = np.linalg.solve(hessian + 1e-10 * np.eye(2), gradient)
        beta += step
        if np.max(np.abs(step)) < tolerance:
            break
    return beta


def b1_probability(frame, hp_unit, beta):
    """Convierte el score fijo de B1 a probabilidad con la sigmoide ajustada."""
    score = b1_score(frame, hp_unit)
    return expit(beta[0] + beta[1] * score)
