"""Seleccion de los casos de validacion y extraccion de sus observaciones.

Todo se elige con la semilla 2026 antes de correr la bateria, y se publica en Kaggle para que
el nivel N1 (Colab) y el N2 (PC con Claude) usen exactamente los mismos estados:
  agente/validacion/casos.csv            una fila por estado elegido
  agente/validacion/observaciones.json   observation['current'] de cada estado (y la preparacion)
  agente/validacion/partidas.json        repeticiones completas para N-06, L-09 y entradas

Reglas (seccion 2 del protocolo):
  - Todos los estados son de partidas de test de A: el modelo del agente nunca las vio.
  - B: partidas de test de A que tambien son de test de B (dias 15 y 22 de julio).
  - C: partidas de test de A que tambien son de test de C (arquetipos reservados).
  - Errores: estados de test de A con p >= 0.9 y derrota, o p <= 0.1 y victoria, segun el
    modelo del agente; se etiquetan por subpoblacion (A completa, B o C).
"""

import json
import tempfile
import time
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
PARTIDAS = f"{CARPETA}/partidas.json"
# Formato anterior: Kaggle no deja bajar el .gz (responde 404), asi que se quita del dataset
PARTIDAS_GZ = f"{CARPETA}/partidas.json.gz"
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


def _limite_de_kaggle(texto):
    return "429" in texto or "Too Many Requests" in texto


def bajar_partida(dia, game_id, carpeta, intentos=6, espera_s=20):
    """JSON de una partida del dataset publico de ese dia. Si Kaggle responde 429 (demasiadas
    peticiones), espera y reintenta: 20 s, 40 s, 80 s... hasta 'intentos' veces."""
    destino = Path(carpeta) / f"{int(game_id)}.json"
    if destino.exists():
        return destino
    texto = ""
    for intento in range(intentos):
        for nombre in (f"{int(game_id)}.json", f"episodes/{int(game_id)}.json"):
            ok, texto = store._bajar_archivo(SLUG.format(day=dia), nombre, destino)
            if ok:
                return destino
            if _limite_de_kaggle(texto):
                break
        if not _limite_de_kaggle(texto):
            break
        espera = espera_s * 2 ** intento
        print(f"   Kaggle pidio esperar (429) en la partida {game_id}: reintento en {espera} s")
        time.sleep(espera)
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


def extraer(casos, larga, raiz, pausa_s=1.0):
    """Baja cada partida una vez, guarda la observacion de cada caso y las repeticiones completas.
    larga = (dia, game_id) de la partida mas larga. Escribe los tres archivos bajo raiz.
    Las descargas van una por una, con una pausa corta, para no pasar el limite de Kaggle."""
    raiz = Path(raiz)
    pedidos = casos.drop_duplicates("game_id")[["day", "game_id"]].values.tolist() + [list(larga)]
    # carpeta fija: si una descarga falla, al reintentar no se bajan otra vez las que ya estan
    carpeta = Path(store.TRABAJO_DIR) / "ptcg-validacion-partidas"
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for k, (dia, g) in enumerate(pedidos, 1):
        ya_estaba = (carpeta / f"{int(g)}.json").exists()
        rutas[int(g)] = bajar_partida(dia, g, carpeta)
        if not ya_estaba:
            time.sleep(pausa_s)
        if k % 20 == 0 or k == len(pedidos):
            print(f"   partidas listas: {k}/{len(pedidos)}")
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
    (raiz / PARTIDAS).write_text(json.dumps({"larga": int(larga[1]), "partidas": completas}),
                                 encoding="utf-8")


def quitar_formato_anterior(raiz):
    """Quita del dataset el partidas.json.gz de la primera corrida (Kaggle responde 404 al
    bajarlo y, mientras siga en el indice, cualquier publicacion desde un servidor nuevo falla).
    Si ya no esta, no hace nada."""
    if PARTIDAS_GZ in store.leer_indice():
        store.eliminar(PARTIDAS_GZ, "agente: quita partidas.json.gz (Kaggle no lo entrega)", raiz)
    else:
        print("formato anterior: no hay partidas.json.gz en el indice")


def casos_publicados(raiz):
    """casos.csv ya publicado (lo baja si hace falta), o None si todavia no existe."""
    if CASOS not in store.leer_indice():
        return None
    store.listo([CASOS], raiz)
    return pd.read_csv(Path(raiz) / CASOS)


def comprobar_misma_eleccion(anterior, elegidos):
    """Al reconstruir, la eleccion debe ser identica a la publicada (misma semilla): si no, los
    resultados de N1 ya publicados no corresponderian a estos casos."""
    if anterior is None:
        return
    claves = ["caso", "game_id", "step"]
    a = anterior[claves].sort_values("caso").reset_index(drop=True)
    b = elegidos[claves].sort_values("caso").reset_index(drop=True)
    if not a.equals(b.astype(a.dtypes.to_dict())):
        raise RuntimeError("la eleccion de casos no coincide con la publicada; no se publica nada")
    print("eleccion identica a la publicada:", len(a), "casos")


class Datos:
    """Casos, observaciones y repeticiones ya publicados, listos para la bateria."""

    def __init__(self, raiz):
        raiz = Path(raiz)
        self.casos = pd.read_csv(raiz / CASOS)
        self.observaciones = json.loads((raiz / OBSERVACIONES).read_text(encoding="utf-8"))
        paquete = json.loads((raiz / PARTIDAS).read_text(encoding="utf-8"))
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