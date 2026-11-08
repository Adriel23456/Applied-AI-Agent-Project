"""Repeticiones reales de ejemplo para probar y demostrar el agente.

Se eligen partidas de test del escenario A de un dia del corpus (nunca vistas por el modelo),
se baja solo el JSON de cada una del dataset publico de Kaggle y se publican en el dataset del
equipo como agente/ejemplos/partida_<id>.json. Asi cualquiera puede probar el agente sin bajar
un dia completo (unos 21 GB).
"""

from pathlib import Path

import numpy as np
import pandas as pd

from ptcg_wp import store
from ptcg_wp.ingest import SLUG

CARPETA = "agente/ejemplos"


def ruta(game_id):
    return f"{CARPETA}/partida_{int(game_id)}.json"


def elegir(datos_dir, dia, n=4, seed=2026):
    """n partidas de test de A de ese dia, de duraciones distintas (cuartiles de pasos)."""
    datos_dir = Path(datos_dir)
    partidas = pd.read_parquet(datos_dir / f"partidas_{dia}.parquet",
                              columns=["game_id", "n_steps", "winner"])
    particiones = pd.read_parquet(datos_dir / "particiones.parquet", columns=["game_id", "split_A"])
    candidatas = partidas.merge(particiones, on="game_id")
    candidatas = candidatas[(candidatas["split_A"] == "test") & (candidatas["winner"] >= 0)]
    if len(candidatas) < n:
        raise RuntimeError(f"solo hay {len(candidatas)} partidas de test de A el {dia}")
    candidatas = candidatas.assign(cuartil=pd.qcut(candidatas["n_steps"], n, labels=False,
                                                   duplicates="drop"))
    rng = np.random.default_rng(seed)
    elegidas = [int(rng.choice(g["game_id"].to_numpy())) for _, g in candidatas.groupby("cuartil")]
    return elegidas[:n]


def bajar(dia, game_id, raiz):
    """Baja el JSON de una partida del dataset publico de ese dia a raiz/agente/ejemplos/."""
    destino = Path(raiz) / ruta(game_id)
    if destino.exists():
        return destino
    slug = SLUG.format(day=dia)
    for nombre in (f"{int(game_id)}.json", f"episodes/{int(game_id)}.json"):
        ok, texto = store._bajar_archivo(slug, nombre, destino)
        if ok:
            return destino
    raise RuntimeError(f"no se pudo bajar la partida {game_id} de {slug}:\n{texto}")


def rutas_publicadas():
    """Ejemplos que ya estan en el dataset del equipo."""
    return sorted(r for r in store.leer_indice() if r.startswith(CARPETA + "/"))