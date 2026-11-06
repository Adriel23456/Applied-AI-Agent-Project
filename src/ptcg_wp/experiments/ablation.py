"""Ablaciones de B4: quitar una familia de caracteristicas y repetir el ajuste final.

La configuracion de B4 (trial 20) y el protocolo se mantienen; solo cambian las columnas.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import time

from ptcg_wp.b4 import fit_b4_candidates_val, materialize_split
from ptcg_wp.data import ScenarioStream


def feature_families(features):
    """Familias mutuamente excluyentes; los nombres se guardan con la corrida."""
    progress = {'game_turn', 'turn_action_count', 'energy_attached', 'retreated',
                'supporter_played', 'stadium_played', 'stadium_in_play', 'first_player_is_me'}
    families = {'progreso': [f for f in features if f in progress],
                'diferenciales': [f for f in features if f.startswith('diff_')]}
    families['recursos_tablero'] = [f for f in features if f not in progress and not f.startswith('diff_')]
    if any(not family for family in families.values()) or sum(map(len, families.values())) != len(features):
        raise ValueError('No se pudieron definir las tres familias de características')
    return families


def run_b4_ablation(data_dir, scenario, features, candidate, output_dir, seed=2026, cache_dir='/content'):
    """Tres variantes: elimina una familia y mantiene configuración y protocolo de B4."""
    families = feature_families(features)
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    (root / 'familias.json').write_text(json.dumps(families, indent=2, ensure_ascii=False))
    for name, removed in families.items():
        selected = [f for f in features if f not in removed]
        out = root / f'sin_{name}'; start = time.perf_counter()
        stream = ScenarioStream(Path(data_dir), scenario, tuple(selected))
        with TemporaryDirectory(prefix='b4-ablation-', dir=cache_dir) as tmp:
            train = materialize_split(stream, selected, 'train', tmp)
            val = materialize_split(stream, selected, 'val', tmp)
            try:
                fit_b4_candidates_val(train, val, candidate, seed=seed, max_iter=4000, patience=30,
                                      monitor_fraction=0.15, max_ram_gib=10.0,
                                      output_dir=out, scenario=scenario, verbose=True)
            finally:
                train.close(); val.close()
        (out / 'duracion.json').write_text(json.dumps({'seconds': time.perf_counter()-start}, indent=2))
