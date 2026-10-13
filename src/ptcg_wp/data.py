"""Carga unica de datos para los cuadernos de modelado (02 en adelante).

Uso tipico:
    from ptcg_wp.data import load_scenario
    states, feats, split, stage = load_scenario("/content/datos", "A")
    X_train = states.loc[split == "train", feats]; y_train = states.loc[split == "train", "y"]
    groups_train = states.loc[split == "train", "game_id"]   # para GroupKFold
"""

from pathlib import Path

import numpy as np
import pandas as pd

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
