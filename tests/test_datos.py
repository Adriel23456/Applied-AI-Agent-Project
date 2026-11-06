"""Prueba de la carga por escenario con tablas Parquet sinteticas en una carpeta temporal."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ptcg_wp.data import load_scenario  # noqa: E402
from ptcg_wp.features import CARD_COLUMNS, game_rows  # noqa: E402
from test_fuga import game  # noqa: E402


def test_load_scenario_filters_and_labels(tmp_path):
    rows = []
    for gid in (1, 2):
        g = game()
        g["info"]["EpisodeId"] = gid
        rows += game_rows(g, "2026-07-01")
    pd.DataFrame(rows).to_parquet(tmp_path / "estados_2026-07-01.parquet", index=False)
    pd.DataFrame({"game_id": [1, 2], "day": ["2026-07-01"] * 2, "split_A": ["train", "test"],
                  "split_B": ["train", "fuera"], "split_C": ["train", "val"]}
                 ).to_parquet(tmp_path / "particiones.parquet", index=False)
    states, feats, split, stage = load_scenario(tmp_path, "A")
    assert (states["setup"] == 0).all() and (states["decided"] == 0).all()
    assert set(split) == {"train", "test"} and len(split) == len(states) == len(stage)
    assert not set(CARD_COLUMNS) & set(feats)
    assert set(stage) <= {"inicio", "medio", "final"}