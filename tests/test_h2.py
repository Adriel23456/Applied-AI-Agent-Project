"""H2: los ids de carta usan TODAS sus categorias aunque superen el limite de 255 de HGB."""

from pathlib import Path
import json
import sys

import joblib
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp.pending_experiments import (codificar_ids_por_bloques, run_h2,  # noqa: E402
                                         vocabulario_ids)


def test_codificacion_por_bloques_es_biyectiva():
    rng = np.random.default_rng(0)
    valores = rng.integers(0, 359, size=5000).astype(np.float32)
    valores[:3] = -1  # centinela de "sin Pokemon activo": es una categoria mas
    vocabulario = vocabulario_ids(valores)
    assert len(vocabulario) == 360
    codigos = codificar_ids_por_bloques(valores, vocabulario)
    assert codigos.shape == (5000, 2)
    # Cada fila tiene exactamente un bloque con valor, y cada bloque cabe en HGB
    assert (np.isfinite(codigos).sum(axis=1) == 1).all()
    assert np.nanmax(codigos) <= 254 and np.nanmin(codigos) >= 0
    # Sin perdida: id -> (bloque, codigo) es uno a uno
    pares = {(int(np.flatnonzero(np.isfinite(f))[0]), int(np.nanmax(f))) for f in codigos}
    assert len(pares) == len(np.unique(valores))
    # Id no visto en train: ausente en todos los bloques
    nuevo = codificar_ids_por_bloques(np.array([999.0, np.nan]), vocabulario)
    assert np.isnan(nuevo).all()


def test_vocabulario_ordena_por_frecuencia_y_luego_por_id():
    assert vocabulario_ids([5, 3, 3, 7, 7, 1]).tolist() == [3, 7, 1, 5]


@pytest.fixture
def corpus(tmp_path):
    rng = np.random.default_rng(11)
    rows, partitions = [], []
    for game in range(1500):
        split = "train" if game < 1200 else "val" if game < 1400 else "test"
        partitions.append({"game_id": f"g{game}", "split_A": split})
        ganador = game % 2
        for turn in range(1, 11):
            # 300 ids distintos (mas de los 255 que admite una columna categorica de HGB):
            # 0-149 solo aparecen en partidas ganadas y 150-299 solo en perdidas
            propio = rng.integers(0, 150) + (0 if ganador else 150)
            rows.append({"game_id": f"g{game}", "turn": turn, "setup": 0, "decided": 0,
                         "y": ganador, "game_turn": turn, "first_player_is_me": int(game % 3 == 0),
                         "own_active_card": int(propio), "opp_active_card": int(rng.integers(0, 300))})
    pd.DataFrame(rows).to_parquet(tmp_path / "estados_1.parquet", index=False)
    pd.DataFrame(partitions).to_parquet(tmp_path / "particiones.parquet", index=False)
    return tmp_path


def test_run_h2_usa_mas_de_255_categorias(corpus, tmp_path):
    salida = tmp_path / "h2"
    run_h2(corpus, "A", salida, seed=3, cache_dir=tmp_path)
    config = json.loads((salida / "h2_config.json").read_text())
    assert config["ids"]["own_active_card"]["categorias_train"] > 255
    assert config["ids"]["own_active_card"]["bloques"] >= 2
    val = pd.read_csv(salida / "h2_val.csv")
    assert set(val["etapa"]) == {"global", "inicio", "medio", "final"}
    # El id propio separa ganadores de perdedores: el modelo debe aprovecharlo
    assert val.loc[val.etapa.eq("global"), "auc"].iloc[0] > 0.9
    artefacto = joblib.load(salida / "h2_restringido.joblib")
    assert len(artefacto["vocabularios"]["own_active_card"]) == config["ids"]["own_active_card"]["categorias_train"]