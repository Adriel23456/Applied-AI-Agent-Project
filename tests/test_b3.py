"""B3 conserva las partidas al muestrear, ajustar y evaluar."""

from pathlib import Path
import sys

import numpy as np
import optuna
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp.baselines import ScenarioStream
from ptcg_wp.b3 import b3_optuna_cv, fit_b3_candidates_val, select_train_games


FEATURES = ["x", "z"]


@pytest.fixture
def corpus(tmp_path):
    rng = np.random.default_rng(31)
    rows, partitions = [], []
    for game in range(25):
        split = "train" if game < 18 else "val" if game < 22 else "test" if game == 22 else "calib"
        game_id = f"g{game}"
        partitions.append({"game_id": game_id, "split_A": split})
        for turn in range(1, 9 + game % 5):
            x, z = rng.normal(size=2)
            rows.append({"game_id": game_id, "turn": turn, "setup": 0, "decided": 0,
                         "y": (game + turn) % 2, "x": x, "z": z})
    states = pd.DataFrame(rows)
    states.iloc[::2].to_parquet(tmp_path / "estados_1.parquet", index=False, row_group_size=23)
    states.iloc[1::2].to_parquet(tmp_path / "estados_2.parquet", index=False, row_group_size=23)
    pd.DataFrame(partitions).to_parquet(tmp_path / "particiones.parquet", index=False)
    return tmp_path, states


def test_b3_group_sample_cv_and_final_val(corpus, tmp_path):
    directory, _ = corpus
    stream = ScenarioStream(directory, "A", tuple(FEATURES), batch_size=13)
    selected_one, available = select_train_games(stream, max_train_games=10, seed=9)
    selected_two, _ = select_train_games(stream, max_train_games=10, seed=9)
    np.testing.assert_array_equal(selected_one, selected_two)
    assert len(selected_one) == 10 and available == 18

    output = tmp_path / "output"
    cv, candidates = b3_optuna_cv(stream, FEATURES, n_splits=2, n_trials=1,
                                  max_folds=1, max_train_games=10, seed=9,
                                  n_jobs=1, max_ram_gib=1,
                                  output_dir=output, verbose=False)
    global_rows = cv.loc[cv.etapa.eq("global")]
    assert set(global_rows.modelo) == {"B3_arbol", "B3_bosque"}
    assert set(global_rows.estudio) == {"auc", "log_loss", "brier"}
    # Piloto con un fold: cinco partidas retenidas para cada modelo/métrica.
    assert global_rows.groupby(["modelo", "estudio"]).partidas_evaluacion.sum().eq(5).all()
    assert global_rows.partidas_train_muestra.eq(10).all()
    assert global_rows.partidas_train_disponibles.eq(18).all()
    assert global_rows.muestreo.eq("partidas_completas_aleatorias").all()
    assert set(candidates.modelo) == {"B3_arbol", "B3_bosque"}
    assert set(candidates.seleccionada_por).issubset({"auc", "log_loss", "brier"})
    assert (output / "b3_cv_A.csv").exists()

    storage = optuna.storages.RDBStorage(url=f"sqlite:///{output / 'b3_optuna.sqlite3'}")
    summaries = optuna.study.get_all_study_summaries(storage=storage)
    assert len(summaries) == 6 and sum(summary.n_trials for summary in summaries) == 6
    resumed_cv, resumed_candidates = b3_optuna_cv(
        stream, FEATURES, n_splits=2, n_trials=1, max_folds=1,
        max_train_games=10, seed=9, n_jobs=1, max_ram_gib=1,
        output_dir=output, verbose=False,
    )
    assert len(resumed_cv) == len(cv)
    pd.testing.assert_frame_equal(resumed_candidates, candidates)
    summaries = optuna.study.get_all_study_summaries(storage=storage)
    assert sum(summary.n_trials for summary in summaries) == 6

    val = fit_b3_candidates_val(stream, FEATURES, candidates, max_train_games=10,
                                seed=9, n_jobs=1, max_ram_gib=1,
                                output_dir=output, verbose=False)
    assert set(val.modelo) == {"B3_arbol", "B3_bosque"}
    assert set(val.seleccionada_por).issubset({"auc", "log_loss", "brier"})
    assert val.loc[val.etapa.eq("global"), "n_partidas"].eq(4).all()
    assert len(list(output.glob("b3_A_*_*.joblib"))) == len(candidates)
    resumed_val = fit_b3_candidates_val(
        stream, FEATURES, candidates, max_train_games=10, seed=9, n_jobs=1,
        max_ram_gib=1, output_dir=output, verbose=False,
    )
    assert len(resumed_val) == len(val)
