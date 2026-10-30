"""Carga de las tablas de estados para modelar: en memoria o por lotes.

- load_scenario: todas las filas utiles de un escenario en RAM (para analisis y pruebas).
- ScenarioStream: las mismas filas leidas por lotes, sin cargar el corpus completo; es lo
  que usan todos los entrenamientos (B0 a B4 y los experimentos).
- weights_by_game: peso 1/n por fila para que cada partida sume 1.

Uso tipico:
    from ptcg_wp.data import load_scenario
    states, feats, split, stage = load_scenario("/content/datos", "A")
    X_train = states.loc[split == "train", feats]; y_train = states.loc[split == "train", "y"]
    groups_train = states.loc[split == "train", "game_id"]   # para GroupKFold
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ptcg_wp.features import feature_columns, usable
from ptcg_wp.splits import assign_stage, stage_cutoffs


def load_states(data_dir, columns=None):
    """Concatena todas las tablas de estados (todas las filas, sin filtrar)."""
    files = sorted(Path(data_dir).glob("estados_*.parquet"))
    return pd.concat((pd.read_parquet(p, columns=columns) for p in files), ignore_index=True)


def load_scenario(data_dir, scenario="A", include_cards=False, columns=None):
    """Filas utiles + particion y etapa de cada fila para un escenario (A, B o C).
    Devuelve (states, feats, split, stage):
      states : DataFrame de filas utiles (sin setup ni estados resueltos), indice 0..n-1
      feats  : columnas de X (sin ids de carta salvo include_cards=True)
      split  : array con train/val/calib/test/fuera por fila
      stage  : array con inicio/medio/final por fila (cortes calculados SOLO con train)

    Si ``columns`` se indica, lee solo esas columnas de los Parquet, más las cinco
    columnas necesarias para filtrar y particionar. Sirve para cuadernos que no
    necesitan las 62 características completas y evita cargar datos innecesarios.
    """
    if columns is not None:
        required = ["game_id", "turn", "setup", "decided", "y"]
        columns = list(dict.fromkeys([*columns, *required]))
    states = usable(load_states(data_dir, columns=columns)).reset_index(drop=True)
    part = pd.read_parquet(Path(data_dir) / "particiones.parquet").set_index("game_id")
    split = states["game_id"].map(part[f"split_{scenario}"]).to_numpy(dtype=object)
    if pd.isna(split).any():
        raise ValueError("hay filas utiles sin particion: regenerar particiones.parquet")
    turns = states["turn"].to_numpy()
    stage = assign_stage(turns, stage_cutoffs(turns[split == "train"]))
    feats = feature_columns(states.columns, include_cards=include_cards)
    return states, feats, split, np.asarray(stage)


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
