"""B4: protocolo agrupado, memmaps y selección sin tocar validación."""

from pathlib import Path
import sys

import numpy as np
import optuna
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp.data import ScenarioStream
from ptcg_wp.b4 import b4_optuna_cv, fit_b4_candidates_val, materialize_split


FEATURES = ["x", "z"]


@pytest.fixture
def corpus(tmp_path):
    rng = np.random.default_rng(51)
    rows, partitions = [], []
    for game in range(26):
        split = "train" if game < 18 else "val" if game < 23 else "test" if game == 23 else "calib"
        game_id = f"g{game}"
        partitions.append({"game_id": game_id, "split_A": split})
        for turn in range(1, 10 + game % 4):
            x, z = rng.normal(size=2)
            # Cada partición conserva ambas clases, incluso en subconjuntos pequeños.
            y = (game + turn) % 2
            rows.append({"game_id": game_id, "turn": turn, "setup": 0,
                         "decided": 0, "y": y, "x": x, "z": z})
    states = pd.DataFrame(rows)
    states.iloc[::2].to_parquet(tmp_path / "estados_1.parquet", index=False, row_group_size=19)
    states.iloc[1::2].to_parquet(tmp_path / "estados_2.parquet", index=False, row_group_size=19)
    pd.DataFrame(partitions).to_parquet(tmp_path / "particiones.parquet", index=False)
    return tmp_path, states


def test_b4_full_train_group_cv_and_val(corpus, tmp_path):
    directory, states = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=11)
    cache, output = tmp_path / "cache", tmp_path / "output"
    cache.mkdir()
    train = materialize_split(stream, FEATURES, "train", cache)
    val = materialize_split(stream, FEATURES, "val", cache)
    assert train.n_rows == states.game_id.isin([f"g{i}" for i in range(18)]).sum()
    assert len(train.games) == 18
    cv, candidates = b4_optuna_cv(train, n_splits=2, n_trials=1, seed=7,
                                  max_iter=12, patience=2, max_ram_gib=1,
                                  output_dir=output, study_cache_dir=tmp_path / "local-one")
    global_rows = cv.loc[cv.etapa.eq("global")]
    # Un solo estudio (log loss) y cobertura externa completa de las 18 partidas.
    assert set(global_rows.estudio) == {"log_loss"}
    assert global_rows.partidas_evaluacion.sum() == 18
    assert (global_rows.partidas_modelo + global_rows.partidas_vigilancia
            + global_rows.partidas_evaluacion).eq(18).all()
    # Las finalistas salen del mismo estudio: una por metrica, sin duplicados.
    assert 1 <= len(candidates) <= 3
    assert set(candidates.seleccionada_por) <= {"auc", "log_loss", "brier"}
    assert (output / "b4_cv_trials.csv").exists()
    assert len(list((output / "fold_checkpoints").glob("b4_*.json"))) == 1

    storage = optuna.storages.RDBStorage(url=f"sqlite:///{output / 'b4_optuna.sqlite3'}")
    summaries = optuna.study.get_all_study_summaries(storage=storage)
    assert len(summaries) == 1 and summaries[0].n_trials == 1
    resumed_cv, resumed_candidates = b4_optuna_cv(
        train, n_splits=2, n_trials=1, seed=7, max_iter=12, patience=2,
        max_ram_gib=1, output_dir=output, study_cache_dir=tmp_path / "local-two",
    )
    assert len(resumed_cv) == len(cv)
    pd.testing.assert_frame_equal(resumed_candidates, candidates)
    summaries = optuna.study.get_all_study_summaries(storage=storage)
    assert summaries[0].n_trials == 1

    val_metrics = fit_b4_candidates_val(train, val, candidates, seed=7,
                                        max_iter=12, patience=2, max_ram_gib=1,
                                        output_dir=output, scenario="A")
    assert set(val_metrics.escenario) == {"A"}
    assert val_metrics.loc[val_metrics.etapa.eq("global"), "partidas_val"].eq(5).all()
    assert len(list(output.glob("b4_*_CVtrial*.joblib"))) == len(candidates)
    resumed_val = fit_b4_candidates_val(
        train, val, candidates, seed=7, max_iter=12, patience=2,
        max_ram_gib=1, output_dir=output, scenario="A",
    )
    assert len(resumed_val) == len(val_metrics)
    train.close()
    val.close()


def test_b4_search_only_uses_allowed_games(corpus, tmp_path):
    """Con search_groups, la validacion cruzada solo usa esas partidas de train."""
    directory, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=11)
    cache = tmp_path / "cache"
    cache.mkdir()
    train = materialize_split(stream, FEATURES, "train", cache)
    allowed = np.arange(0, len(train.games), 2)
    cv, _ = b4_optuna_cv(train, n_splits=2, n_trials=1, seed=7, max_iter=12, patience=2,
                         max_ram_gib=1, search_groups=allowed)
    global_rows = cv.loc[cv.etapa.eq("global")]
    assert global_rows.partidas_evaluacion.sum() == len(allowed)
    assert (global_rows.partidas_modelo + global_rows.partidas_vigilancia
            + global_rows.partidas_evaluacion).eq(len(allowed)).all()