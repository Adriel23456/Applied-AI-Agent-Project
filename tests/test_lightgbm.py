"""LightGBM: busqueda, ajuste final y comparacion con B4 sin avisos de nombres de columnas."""

from pathlib import Path
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

lgb = pytest.importorskip("lightgbm")

from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402

from ptcg_wp.experiments.lightgbm_vs_b4 import compare_lightgbm_b4, run_lightgbm  # noqa: E402

FEATURES = ["x", "z"]


@pytest.fixture
def corpus(tmp_path):
    rng = np.random.default_rng(7)
    rows, partitions = [], []
    for game in range(60):
        split = "train" if game < 40 else "val" if game < 52 else "test"
        partitions.append({"game_id": f"g{game}", "split_A": split, "split_B": split, "split_C": split})
        ganador = game % 2
        for turn in range(1, 12):
            x, z = rng.normal(size=2)
            rows.append({"game_id": f"g{game}", "turn": turn, "setup": 0, "decided": 0,
                         "y": ganador, "x": x + ganador, "z": z})
    pd.DataFrame(rows).to_parquet(tmp_path / "estados_1.parquet", index=False)
    pd.DataFrame(partitions).to_parquet(tmp_path / "particiones.parquet", index=False)
    return tmp_path


def test_lightgbm_sin_aviso_de_nombres(corpus, tmp_path):
    estados = pd.read_parquet(corpus / "estados_1.parquet")
    train = estados[estados.game_id.isin([f"g{i}" for i in range(40)])]
    b4_root = tmp_path / "b4"
    for escenario in "ABC":
        modelo = HistGradientBoostingClassifier(max_iter=5).fit(train[FEATURES].to_numpy(), train.y)
        (b4_root / f"escenario_{escenario}").mkdir(parents=True)
        joblib.dump({"model": modelo, "features": FEATURES},
                    b4_root / f"escenario_{escenario}" / "b4_auc_CVtrial20.joblib")
    salida = tmp_path / "lightgbm"
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        run_lightgbm(corpus, FEATURES, salida, seed=3, cache_dir=tmp_path, n_jobs=1)
        _, decision = compare_lightgbm_b4(corpus, b4_root, salida, seed=3)
    nombres = [str(a.message) for a in avisos if "feature names" in str(a.message)]
    assert nombres == []
    assert decision["decision"] in {"mantener_b4", "seleccionar_lightgbm"}
    trial = int(pd.read_csv(salida / "lightgbm_finalista.csv").iloc[0]["trial"])
    modelo = joblib.load(salida / "escenario_A" / f"lightgbm_trial_{trial}.joblib")["model"]
    assert list(modelo.feature_names_in_) == FEATURES