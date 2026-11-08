"""Seleccion de los casos de validacion y extraccion de sus observaciones.

Todo se elige con la semilla 2026 antes de correr la bateria, y se publica en Kaggle para que
el nivel N1 (Colab) y el N2 (PC con Claude) usen exactamente los mismos estados:
  agente/validacion/casos.csv            una fila por estado elegido
  agente/validacion/observaciones.json   observation['current'] de cada estado (y la preparacion)
  agente/validacion/partidas.json.gz     repeticiones completas para N-06, L-09 y entradas

Reglas (seccion 2 del protocolo):
  - Todos los estados son de partidas de test de A: el modelo del agente nunca las vio.
  - B: partidas de test de A que tambien son de test de B (dias 15 y 22 de julio).
  - C: partidas de test de A que tambien son de test de C (arquetipos reservados).
  - Errores: estados de test de A con p >= 0.9 y derrota, o p <= 0.1 y victoria, segun el
    modelo del agente; se etiquetan por subpoblacion (A completa, B o C).
"""

import gzip
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from ptcg_wp import store
from ptcg_wp.evaluacion_final import cargar_particion
from ptcg_wp.features import acting_player
from ptcg_wp.ingest import SLUG

SEMILLA = 2026
CARPETA = "agente/validacion"
CASOS = f"{CARPETA}/casos.csv"
OBSERVACIONES = f"{CARPETA}/observaciones.json"
PARTIDAS = f"{CARPETA}/partidas.json.gz"
ETAPAS = ("inicio", "medio", "final")
SEGURO = 0.9
N_REPETICIONES = 10


def tabla_test_a(data_dir, predictor):
    """Estados utiles de test de A con la probabilidad del modelo del agente y la subpoblacion."""
    tabla = cargar_particion(data_dir, "A", "test", ["day", "step", *predictor.features])
    tabla["p"] = predictor.probabilidades_tabla(tabla)
    part = pd.read_parquet(Path(data_dir) / "particiones.parquet",
                           columns=["game_id", "split_B", "split_C"]).set_index("game_id")
    tabla["en_B"] = tabla["game_id"].map(part["split_B"]).eq("test").to_numpy()
    tabla["en_C"] = tabla["game_id"].map(part["split_C"]).eq("test").to_numpy()
    return tabla[["game_id", "day", "step", "turn", "stage", "y", "p", "en_B", "en_C"]]


def _una_por_etapa(tabla, partidas, rng, grupo, prefijo):
    filas = []
    for k, g in enumerate(partidas):
        estados = tabla[tabla["game_id"] == g]
        for etapa in ETAPAS:
            opciones = estados[estados["stage"] == etapa]
            fila = opciones.iloc[int(rng.integers(len(opciones)))]
            filas.append({**fila.to_dict(), "grupo": grupo, "caso": f"{prefijo}-{etapa}-{k:02d}"})
    return filas


def _partidas_completas(tabla, mascara, excluir, n, rng):
    """n partidas con estados en las tres etapas, sin repetir las ya elegidas."""
    sub = tabla[mascara & ~tabla["game_id"].isin(excluir)]
    etapas = sub.groupby("game_id")["stage"].nunique()
    candidatas = np.sort(etapas[etapas == len(ETAPAS)].index.to_numpy())
    if len(candidatas) < n:
        raise RuntimeError(f"solo hay {len(candidatas)} partidas con las tres etapas")
    return [int(g) for g in rng.choice(candidatas, size=n, replace=False)]


def elegir(tabla, n=30, n_errores=10, seed=SEMILLA):
    """Casos de la seccion 2 del protocolo. Devuelve un DataFrame con una fila por estado."""
    rng = np.random.default_rng(seed)
    todas = np.ones(len(tabla), dtype=bool)
    a = _partidas_completas(tabla, todas, [], n, rng)
    b = _partidas_completas(tabla, tabla["en_B"].to_numpy(), a, n, rng)
    c = _partidas_completas(tabla, tabla["en_C"].to_numpy(), a + b, n, rng)
    filas = (_una_por_etapa(tabla, a, rng, "normal_A", "A")
             + _una_por_etapa(tabla, b, rng, "poblacion_B", "B")
             + _una_por_etapa(tabla, c, rng, "poblacion_C", "C"))
    seguro_mal = ((tabla["p"] >= SEGURO) & (tabla["y"] == 0)) | ((tabla["p"] <= 1 - SEGURO) & (tabla["y"] == 1))
    for sub, mascara in (("A", todas), ("B", tabla["en_B"].to_numpy()), ("C", tabla["en_C"].to_numpy())):
        for etapa in ETAPAS:
            errores = tabla[seguro_mal.to_numpy() & mascara & (tabla["stage"] == etapa).to_numpy()]
            errores = errores.iloc[rng.permutation(len(errores))].drop_duplicates("game_id")
            for k, (_, fila) in enumerate(errores.head(n_errores).iterrows()):
                filas.append({**fila.to_dict(), "grupo": f"error_{sub}", "caso": f"M{sub}-{etapa}-{k:02d}"})
    casos = pd.DataFrame(filas)
    casos["completa"] = casos["game_id"].isin(a[:N_REPETICIONES])
    casos[["game_id", "step", "turn", "y"]] = casos[["game_id", "step", "turn", "y"]].astype(int)
    return casos[["caso", "grupo", "game_id", "day", "step", "turn", "stage", "y", "p", "en_B", "en_C",
                  "completa"]]


def partida_mas_larga(data_dir, tabla):
    """(dia, game_id) de la partida de test de A con mas pasos."""
    partidas = pd.concat(pd.read_parquet(p, columns=["game_id", "n_steps"])
                         for p in sorted(Path(data_dir).glob("partidas_*.parquet")))
    dias = tabla.drop_duplicates("game_id").set_index("game_id")["day"]
    partidas = partidas[partidas["game_id"].isin(dias.index)].sort_values(["n_steps", "game_id"])
    g = int(partidas.iloc[-1]["game_id"])
    return str(dias.loc[g]), g


def bajar_partida(dia, game_id, carpeta):
    """JSON de una partida del dataset publico de ese dia."""
    destino = Path(carpeta) / f"{int(game_id)}.json"
    if destino.exists():
        return destino
    texto = ""
    for nombre in (f"{int(game_id)}.json", f"episodes/{int(game_id)}.json"):
        ok, texto = store._bajar_archivo(SLUG.format(day=dia), nombre, destino)
        if ok:
            return destino
    raise RuntimeError(f"no se pudo bajar la partida {game_id} del {dia}:\n{texto}")


def observacion(repeticion, paso):
    j = acting_player(repeticion["steps"][paso])
    return repeticion["steps"][paso][j]["observation"]["current"]


def preparacion(repeticion):
    """Primera observacion real de turno 0 del jugador que actua (L-01)."""
    for paso in repeticion["steps"]:
        j = acting_player(paso)
        cur = (paso[j].get("observation") or {}).get("current") if j is not None else None
        if cur and cur.get("turn") == 0:
            return cur
    raise RuntimeError("la repeticion no tiene una observacion de preparacion")


def extraer(casos, larga, raiz, hilos=8):
    """Baja cada partida una vez, guarda la observacion de cada caso y las repeticiones completas.
    larga = (dia, game_id) de la partida mas larga. Escribe los tres archivos bajo raiz."""
    raiz = Path(raiz)
    pedidos = casos.drop_duplicates("game_id")[["day", "game_id"]].values.tolist() + [list(larga)]
    # carpeta fija: si una descarga falla, al reintentar no se bajan otra vez las que ya estan
    carpeta = Path(store.TRABAJO_DIR) / "ptcg-validacion-partidas"
    carpeta.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(hilos) as ex:
        rutas = dict(zip([int(g) for _, g in pedidos],
                         ex.map(lambda dg: bajar_partida(dg[0], dg[1], carpeta), pedidos)))
    observaciones, completas = {}, {}
    for g, ruta in rutas.items():
        rep = json.loads(Path(ruta).read_text(encoding="utf-8"))
        for _, c in casos[casos["game_id"] == g].iterrows():
            observaciones[c["caso"]] = observacion(rep, int(c["step"]))
        if g == int(larga[1]) or casos.loc[casos["game_id"] == g, "completa"].any():
            completas[str(g)] = rep
    primera = int(casos.loc[casos["completa"], "game_id"].iloc[0])
    observaciones["preparacion"] = preparacion(completas[str(primera)])
    (raiz / CARPETA).mkdir(parents=True, exist_ok=True)
    casos.assign(larga=casos["game_id"].eq(int(larga[1]))).to_csv(raiz / CASOS, index=False)
    (raiz / OBSERVACIONES).write_text(json.dumps(observaciones), encoding="utf-8")
    with gzip.open(raiz / PARTIDAS, "wt", encoding="utf-8") as f:
        json.dump({"larga": int(larga[1]), "partidas": completas}, f)


class Datos:
    """Casos, observaciones y repeticiones ya publicados, listos para la bateria."""

    def __init__(self, raiz):
        raiz = Path(raiz)
        self.casos = pd.read_csv(raiz / CASOS)
        self.observaciones = json.loads((raiz / OBSERVACIONES).read_text(encoding="utf-8"))
        with gzip.open(raiz / PARTIDAS, "rt", encoding="utf-8") as f:
            paquete = json.load(f)
        self.carpeta = Path(tempfile.mkdtemp(prefix="ptcg-partidas-"))
        self.repeticiones = {}
        for g, rep in paquete["partidas"].items():
            ruta = self.carpeta / f"partida_{g}.json"
            ruta.write_text(json.dumps(rep), encoding="utf-8")
            self.repeticiones[int(g)] = ruta
        self.larga = int(paquete["larga"])

    def grupo(self, nombre, etapa=None):
        sub = self.casos[self.casos["grupo"] == nombre]
        if etapa is not None:
            sub = sub[sub["stage"] == etapa]
        return sub.sort_values("caso")

    def obs(self, caso):
        return self.observaciones[caso]