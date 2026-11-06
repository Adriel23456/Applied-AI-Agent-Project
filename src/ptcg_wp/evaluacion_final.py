"""Evaluacion final (rama 05FinalModelChecks): test, calibracion, hipotesis, errores, SHAP y curvas.

El protocolo y las reglas de decision estan en
docx/03Evidence/02-11-26_ProtocoloEvaluacionFinal.md, escrito antes de abrir test. Este modulo
solo tiene la logica; se ejecuta desde las celdas de notebooks/06_evaluacion_final.ipynb.

Reglas que aplica todo el modulo:
- Cada partida pesa lo mismo (1/n por estado, recalculado dentro de cada grupo).
- Los intervalos remuestrean partidas completas; las comparaciones entre modelos son emparejadas
  (mismas multiplicidades de partida en ambos).
- Las cifras por escenario nunca se promedian ni se mezclan.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import joblib
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.special import logit
from sklearn.isotonic import IsotonicRegression, isotonic_regression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from ptcg_wp.b0_b1 import b1_probability
from ptcg_wp.b2_streaming import game_counts
from ptcg_wp.b4 import fit_b4_candidates_val, materialize_split
from ptcg_wp.data import ScenarioStream
from ptcg_wp.evaluation import STAGES, metric_rows_codes
from ptcg_wp.experiments.ablation import feature_families
from ptcg_wp.experiments.h2 import codificar_ids_por_bloques
from ptcg_wp.features import CARD_COLUMNS, FORBIDDEN_IN_X
from ptcg_wp.model_comparison import _auc_from_plan, _auc_sort_plan

MODELOS = ("B0", "B1", "B2", "B3", "B4", "H2")
METRICAS = ("auc", "log_loss", "brier")
GRUPOS = ("global", *STAGES)
METODOS = ("ninguna", "isotonica", "platt")
N_BOOT = 1000
SEMILLA = 2026
EPS = 1e-15

MODELO_B2 = "b2/final/escenario_{e}/b2_{e}_C0.1.joblib"
MODELO_B3 = "b3/final/escenario_{e}/b3_{e}_B3_bosque_log_loss.joblib"
MODELO_B4 = "b4/final/escenario_{e}/b4_auc_CVtrial20.joblib"
MODELO_H2 = "b4/h2/escenario_{e}/h2_restringido.joblib"
AJUSTES_B0_B1 = "b0_b1/ajustes_B0_B1.csv"


# ----------------------------------------------------------------------------------------
# Datos y predicciones
# ----------------------------------------------------------------------------------------

def cargar_particion(data_dir, escenario, particion, columnas):
    """Filas utiles de una particion, con su etapa, en memoria. Abre calib y test a proposito."""
    stream = ScenarioStream(Path(data_dir), escenario, tuple(columnas), evaluacion_final=True)
    partes = list(stream.iter_batches(particion, columns=list(columnas)))
    if not partes:
        raise ValueError(f"no hay estados en {particion} de {escenario}")
    return pd.concat(partes, ignore_index=True)


def predecir_h2(artefacto, tabla):
    """Predicciones de H2 con la misma codificacion por bloques del ajuste."""
    partes = [tabla[["game_turn", "first_player_is_me"]].to_numpy(dtype=np.float32)]
    for nombre in CARD_COLUMNS:
        partes.append(codificar_ids_por_bloques(tabla[nombre].to_numpy(),
                                                np.asarray(artefacto["vocabularios"][nombre]),
                                                artefacto["categorias_por_bloque"]))
    return artefacto["model"].predict_proba(np.hstack(partes).astype(np.float32))[:, 1]


def predicciones_particion(data_dir, raiz, escenario, particion, features):
    """Una fila por estado con la probabilidad de B0 a B4 y de H2 (columnas p_<modelo>).

    Usa los artefactos ya entrenados de cada escenario; aqui no se ajusta nada.
    """
    raiz = Path(raiz)
    columnas = list(dict.fromkeys(["day", "step", *features, *CARD_COLUMNS]))
    tabla = cargar_particion(data_dir, escenario, particion, columnas)
    ajustes = pd.read_csv(raiz / AJUSTES_B0_B1).set_index("escenario").loc[escenario]
    salida = tabla[["game_id", "day", "step", "turn", "stage", "y"]].copy()
    salida["p_B0"] = float(ajustes["prevalencia_B0_train"])
    salida["p_B1"] = b1_probability(tabla, float(ajustes["hp_unit_train"]),
                                    (float(ajustes["intercepto_B1"]), float(ajustes["pendiente_B1"])))
    for nombre, patron, tipo in (("B2", MODELO_B2, np.float64), ("B3", MODELO_B3, np.float64),
                                 ("B4", MODELO_B4, np.float32)):
        item = joblib.load(raiz / patron.format(e=escenario))
        if list(item["features"]) != list(features):
            raise ValueError(f"{nombre} {escenario} no usa las caracteristicas esperadas")
        salida[f"p_{nombre}"] = item["model"].predict_proba(
            tabla[list(features)].to_numpy(dtype=tipo))[:, 1]
        del item
    h2 = joblib.load(raiz / MODELO_H2.format(e=escenario))
    salida["p_H2"] = predecir_h2(h2, tabla)
    salida["id_desconocido"] = np.logical_or.reduce(
        [~tabla[c].isin(h2["vocabularios"][c]).to_numpy() for c in CARD_COLUMNS])
    return salida


def metricas_val_guardadas(raiz, escenario):
    """Metricas de val que los cuadernos 02 a 05 publicaron para cada modelo de la escalera."""
    raiz = Path(raiz)
    b0_b1 = pd.read_csv(raiz / "b0_b1/metricas_B0_B1.csv")
    b0_b1 = b0_b1.loc[b0_b1["escenario"].eq(escenario)]
    b2 = pd.read_csv(raiz / f"b2/final/escenario_{escenario}/b2_val_{escenario}.csv")
    b3 = pd.read_csv(raiz / f"b3/final/escenario_{escenario}/b3_val_{escenario}.csv")
    b4 = pd.read_csv(raiz / f"b4/final/escenario_{escenario}/b4_val_finalistas.csv")
    h2 = pd.read_csv(raiz / f"b4/h2/escenario_{escenario}/h2_val.csv")
    partes = {"B0": b0_b1.loc[b0_b1["modelo"].eq("B0")], "B1": b0_b1.loc[b0_b1["modelo"].eq("B1")],
              "B2": b2.loc[b2["C"].eq(0.1)],
              "B3": b3.loc[b3["modelo"].eq("B3_bosque") & b3["seleccionada_por"].eq("log_loss")],
              "B4": b4.loc[b4["trial"].eq(20)], "H2": h2}
    return pd.concat([p[["etapa", *METRICAS, "n_estados", "n_partidas"]].assign(modelo=m)
                      for m, p in partes.items()], ignore_index=True)


def verificar_contra_val(tabla, raiz, escenario):
    """Barrera antes de abrir test: las predicciones de este modulo deben reproducir las
    metricas de val ya publicadas. Si no, hay un error de carga y test no se toca.

    Log loss y Brier son la prueba estricta. El AUC se compara aparte porque B3 tiene empates
    exactos: su bosque paralelo suma los arboles en distinto orden en cada lote, eso cambia el
    ultimo bit de algunas filas (2e-16) y rompe empates, asi que evaluate_stream da un AUC que
    varia un poco con el tamano de lote. Con n_jobs=1 la diferencia desaparece."""
    medidas, _ = evaluar_con_intervalos(tabla, MODELOS, {}, n_boot=100)
    unidas = medidas.merge(metricas_val_guardadas(raiz, escenario), on=["modelo", "etapa"],
                           suffixes=("_medido", "_guardado"), validate="one_to_one")
    if len(unidas) != len(MODELOS) * len(GRUPOS):
        raise ValueError(f"faltan metricas guardadas de {escenario}: {len(unidas)} filas")
    if not unidas["n_estados_medido"].equals(unidas["n_estados_guardado"]):
        raise ValueError(f"{escenario}: el numero de estados no coincide con el publicado")
    unidas["dif_auc"] = (unidas["auc_medido"] - unidas["auc_guardado"]).abs()
    unidas["dif_puntajes"] = np.max([(unidas[f"{m}_medido"] - unidas[f"{m}_guardado"]).abs()
                                     for m in ("log_loss", "brier")], axis=0)
    return unidas[["modelo", "etapa", "auc_medido", "auc_guardado", "dif_auc", "dif_puntajes"]]


def codigos_partida(game_ids):
    """Ids de partida -> codigos enteros contiguos desde 0."""
    return pd.factorize(np.asarray(game_ids), sort=True)[0].astype(np.int64)


def codigos_etapa(etapas):
    return pd.Series(etapas).map({s: c for c, s in enumerate(STAGES)}).to_numpy(dtype=np.int8)


def pesos_partida(codigos):
    """Peso 1/n por estado, con n = estados de la partida dentro de este grupo."""
    return 1.0 / np.bincount(codigos)[codigos]


# ----------------------------------------------------------------------------------------
# Remuestreo por partida
# ----------------------------------------------------------------------------------------

def multiplicidades(n_partidas, n_boot=N_BOOT, seed=SEMILLA):
    """Cuantas veces entra cada partida en cada replica. Misma semilla = mismas replicas."""
    rng = np.random.default_rng(seed)
    for _ in range(n_boot):
        yield rng.multinomial(n_partidas, np.full(n_partidas, 1 / n_partidas))


class _PlanMetricas:
    """Lo necesario para recalcular AUC, log loss y Brier con otras multiplicidades de partida.
    Ordena una sola vez y resume por partida, asi cada replica no recorre todo de nuevo."""

    def __init__(self, y, p, codigos, n_partidas):
        y = np.asarray(y, dtype=np.float64)
        p = np.clip(np.asarray(p, dtype=np.float64), EPS, 1 - EPS)
        pesos = pesos_partida(codigos)
        self.auc = _auc_sort_plan(y, p, codigos)
        self.peso = np.bincount(codigos, pesos, n_partidas)
        perdida = -(y * np.log(p) + (1 - y) * np.log1p(-p))
        self.log_loss = np.bincount(codigos, pesos * perdida, n_partidas)
        self.brier = np.bincount(codigos, pesos * (y - p) ** 2, n_partidas)

    def medir(self, multiplicidad):
        total = multiplicidad @ self.peso
        if total == 0:
            return {m: np.nan for m in METRICAS}
        return {"auc": _auc_from_plan(self.auc, multiplicidad),
                "log_loss": float(multiplicidad @ self.log_loss / total),
                "brier": float(multiplicidad @ self.brier / total)}


def replicar(y, predicciones, codigos, grupos, n_boot=N_BOOT, seed=SEMILLA):
    """Replicas {(modelo, grupo, metrica): array}. Todos los modelos y grupos comparten las
    multiplicidades, de modo que cualquier resta entre replicas es una comparacion emparejada."""
    y, codigos = np.asarray(y), np.asarray(codigos)
    n_partidas = int(codigos.max()) + 1
    planes = {(modelo, grupo): _PlanMetricas(y[mascara], np.asarray(p)[mascara], codigos[mascara], n_partidas)
              for modelo, p in predicciones.items()
              for grupo, mascara in grupos.items() if mascara.any()}
    replicas = {(*clave, m): np.empty(n_boot) for clave in planes for m in METRICAS}
    for i, multiplicidad in enumerate(multiplicidades(n_partidas, n_boot, seed)):
        for clave, plan in planes.items():
            for m, valor in plan.medir(multiplicidad).items():
                replicas[(*clave, m)][i] = valor
    return replicas


def intervalo(replica):
    """Intervalo percentil del 95 %. Falla si demasiadas replicas no tienen ambas clases."""
    validas = replica[np.isfinite(replica)]
    if len(validas) < 0.95 * len(replica):
        raise ValueError("demasiadas replicas sin ambas clases en este grupo")
    inferior, superior = np.quantile(validas, [0.025, 0.975])
    return float(inferior), float(superior)


def grupos_etapa(etapas):
    etapas = np.asarray(etapas)
    return {"global": np.ones(len(etapas), dtype=bool), **{s: etapas == s for s in STAGES}}


def evaluar_con_intervalos(tabla, modelos, comun, n_boot=N_BOOT, seed=SEMILLA):
    """Metricas de la funcion comun, globales y por etapa, con su intervalo por partida.
    Devuelve (DataFrame de metricas, replicas)."""
    y = tabla["y"].to_numpy(dtype=np.uint8)
    codigos = codigos_partida(tabla["game_id"])
    etapas = tabla["stage"].to_numpy()
    predicciones = {m: tabla[f"p_{m}"].to_numpy() for m in modelos}
    replicas = replicar(y, predicciones, codigos, grupos_etapa(etapas), n_boot, seed)
    filas = []
    for modelo, p in predicciones.items():
        for fila in metric_rows_codes(y, p, codigos, codigos_etapa(etapas), {**comun, "modelo": modelo}):
            for m in METRICAS:
                fila[f"{m}_ic_inf"], fila[f"{m}_ic_sup"] = intervalo(replicas[(modelo, fila["etapa"], m)])
            filas.append(fila)
    return pd.DataFrame(filas), replicas


def comparar(metricas, replicas, principal, referencias, comun):
    """Diferencia emparejada principal - referencia por etapa y metrica, con su intervalo."""
    filas = []
    puntos = metricas.set_index(["modelo", "etapa"])
    for referencia in referencias:
        for etapa in puntos.loc[principal].index:
            for m in METRICAS:
                resta = replicas[(principal, etapa, m)] - replicas[(referencia, etapa, m)]
                inferior, superior = intervalo(resta)
                filas.append({**comun, "principal": principal, "referencia": referencia, "etapa": etapa,
                              "metrica": m, "valor_principal": puntos.loc[(principal, etapa), m],
                              "valor_referencia": puntos.loc[(referencia, etapa), m],
                              "delta": puntos.loc[(principal, etapa), m] - puntos.loc[(referencia, etapa), m],
                              "ic_inf": inferior, "ic_sup": superior})
    return pd.DataFrame(filas)


def criterio_b1(metricas, principal="B4", referencia="B1"):
    """Criterio interno de la Seccion III-D: supera a B1 con intervalos de AUC sin solaparse."""
    filas = metricas.loc[metricas["etapa"].eq("global")].set_index("modelo")
    p, r = filas.loc[principal], filas.loc[referencia]
    return {"auc_principal": float(p["auc"]), "auc_referencia": float(r["auc"]),
            "cumple": bool(p["auc"] > r["auc"] and p["auc_ic_inf"] > r["auc_ic_sup"])}


def auc_por_turno(tabla, modelo="B4", tope=20, n_boot=N_BOOT, seed=SEMILLA):
    """Curva de AUC por turno, con el ultimo punto agrupando los turnos >= tope."""
    turnos = np.minimum(tabla["turn"].to_numpy(), tope)
    codigos = codigos_partida(tabla["game_id"])
    grupos = {int(t): turnos == t for t in np.unique(turnos)}
    y = tabla["y"].to_numpy(dtype=np.uint8)
    replicas = replicar(y, {modelo: tabla[f"p_{modelo}"].to_numpy()}, codigos, grupos, n_boot, seed)
    p = tabla[f"p_{modelo}"].to_numpy()
    filas = []
    for turno, mascara in grupos.items():
        punto = metric_rows_codes(y[mascara], p[mascara], codigos[mascara], None, {},
                                  include_stages=False)[0]
        inferior, superior = intervalo(replicas[(modelo, turno, "auc")])
        filas.append({"turno": turno, "auc": punto["auc"], "auc_ic_inf": inferior, "auc_ic_sup": superior,
                      "n_estados": punto["n_estados"], "n_partidas": punto["n_partidas"]})
    return pd.DataFrame(filas)


def primer_turno_banda(curva, umbral=0.78):
    """Primer turno cuyo AUC puntual alcanza la banda de literatura (None si no la alcanza)."""
    alcanzan = curva.loc[curva["auc"] >= umbral, "turno"]
    return int(alcanzan.min()) if len(alcanzan) else None


# ----------------------------------------------------------------------------------------
# Calibracion
# ----------------------------------------------------------------------------------------

def ajustar_calibrador(metodo, p, y, pesos):
    """Calibrador ajustado con (p, y). 'ninguna' es la identidad, para compararla igual."""
    p, y = np.asarray(p, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if metodo == "ninguna":
        return {"metodo": metodo, "modelo": None}
    if metodo == "isotonica":
        modelo = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        return {"metodo": metodo, "modelo": modelo.fit(p, y, sample_weight=pesos)}
    if metodo == "platt":
        x = logit(np.clip(p, 1e-6, 1 - 1e-6)).reshape(-1, 1)
        modelo = LogisticRegression(penalty=None, solver="lbfgs", max_iter=1000)
        return {"metodo": metodo, "modelo": modelo.fit(x, y, sample_weight=pesos)}
    raise ValueError(f"metodo de calibracion desconocido: {metodo}")


def aplicar_calibrador(calibrador, p):
    p = np.asarray(p, dtype=np.float64)
    if calibrador["metodo"] == "ninguna":
        return p
    if calibrador["metodo"] == "isotonica":
        return calibrador["modelo"].predict(p)
    return calibrador["modelo"].predict_proba(logit(np.clip(p, 1e-6, 1 - 1e-6)).reshape(-1, 1))[:, 1]


def validar_calibradores(p, y, codigos, n_pliegues=5, seed=SEMILLA):
    """Compara los metodos DENTRO de calib con pliegues por partida. Es la decision del
    articulo de medir antes de corregir, y no consulta test."""
    p, y = np.asarray(p, dtype=np.float64), np.asarray(y, dtype=np.float64)
    fuera = {m: np.empty(len(p)) for m in METODOS}
    pliegues = GroupKFold(n_splits=n_pliegues, shuffle=True, random_state=seed).split(p, y, codigos)
    for ajuste, retenido in pliegues:
        pesos = pesos_partida(codigos_partida(codigos[ajuste]))
        for metodo in METODOS:
            fuera[metodo][retenido] = aplicar_calibrador(
                ajustar_calibrador(metodo, p[ajuste], y[ajuste], pesos), p[retenido])
    return pd.DataFrame([metric_rows_codes(y, fuera[m], codigos, None, {"metodo": m}, include_stages=False)[0]
                         for m in METODOS])


def elegir_metodo(validacion):
    """Menor log loss fuera de pliegue. Se fija antes de abrir test."""
    return str(validacion.sort_values(["log_loss", "brier"]).iloc[0]["metodo"])


class _PlanCorp:
    """Descomposicion CORP (Dimitriadis et al.): puntaje = MCB - DSC + UNC.

    La recalibracion PAV sobre el propio conjunto evaluado separa calibracion (MCB) de
    ordenamiento (DSC) en las MISMAS unidades del puntaje, con pesos por partida. Es el
    instrumento de la Figura 6 del articulo y la base de la regla de H3."""

    def __init__(self, y, p, codigos):
        p = np.clip(np.asarray(p, dtype=np.float64), EPS, 1 - EPS)
        orden = np.argsort(p, kind="mergesort")
        self.p = p[orden]
        self.y = np.asarray(y, dtype=np.float64)[orden]
        self.codigos = np.asarray(codigos)[orden]
        self.pesos = 1.0 / np.bincount(codigos)[self.codigos]
        self.inicios = np.flatnonzero(np.r_[True, self.p[1:] != self.p[:-1]])
        self.valores = self.p[self.inicios]

    @staticmethod
    def _puntajes(q, peso, positivos):
        q = np.clip(q, EPS, 1 - EPS)
        total = peso.sum()
        negativos = peso - positivos
        return {"log_loss": float(-(positivos * np.log(q) + negativos * np.log1p(-q)).sum() / total),
                "brier": float((positivos * (1 - q) ** 2 + negativos * q ** 2).sum() / total)}

    def medir(self, multiplicidad=None):
        w = self.pesos if multiplicidad is None else self.pesos * multiplicidad[self.codigos]
        peso = np.add.reduceat(w, self.inicios)
        positivos = np.add.reduceat(w * self.y, self.inicios)
        vivos = peso > 0
        peso, positivos, valores = peso[vivos], positivos[vivos], self.valores[vivos]
        pav = isotonic_regression(positivos / peso, sample_weight=peso, increasing=True)
        base = positivos.sum() / peso.sum()
        original = self._puntajes(valores, peso, positivos)
        recalibrado = self._puntajes(pav, peso, positivos)
        referencia = self._puntajes(np.full(len(peso), base), peso, positivos)
        salida = {}
        for s in ("log_loss", "brier"):
            salida[f"{s}_puntaje"] = original[s]
            salida[f"{s}_mcb"] = original[s] - recalibrado[s]
            salida[f"{s}_dsc"] = referencia[s] - recalibrado[s]
            salida[f"{s}_unc"] = referencia[s]
        return salida


def descomposicion_corp(y, p, codigos):
    """MCB, DSC y UNC de log loss y Brier (cifras puntuales, cada partida con el mismo peso)."""
    return _PlanCorp(y, p, np.asarray(codigos)).medir()


def tabla_fiabilidad(y, p, codigos, n_bins=10):
    """Diagrama de fiabilidad en intervalos de igual masa, con cada partida con el mismo peso."""
    y, p = np.asarray(y, dtype=np.float64), np.asarray(p, dtype=np.float64)
    pesos = pesos_partida(np.asarray(codigos))
    orden = np.argsort(p, kind="mergesort")
    acumulado = np.cumsum(pesos[orden]) / pesos.sum()
    bins = np.minimum((acumulado * n_bins).astype(int), n_bins - 1)
    tabla = pd.DataFrame({"bin": bins, "w": pesos[orden], "wp": pesos[orden] * p[orden],
                          "wy": pesos[orden] * y[orden], "n": 1}).groupby("bin").sum()
    return pd.DataFrame({"bin": tabla.index, "p_media": tabla["wp"] / tabla["w"],
                         "y_media": tabla["wy"] / tabla["w"], "peso": tabla["w"] / pesos.sum(),
                         "n_estados": tabla["n"]}).reset_index(drop=True)


def ece(fiabilidad):
    """Error de calibracion esperado a partir de una tabla de fiabilidad."""
    return float((fiabilidad["peso"] * (fiabilidad["p_media"] - fiabilidad["y_media"]).abs()).sum())


# ----------------------------------------------------------------------------------------
# Hipotesis
# ----------------------------------------------------------------------------------------

def prueba_h1(tabla, escenario, modelo="B4", n_boot=N_BOOT, seed=SEMILLA):
    """H1: (a) senal clara en 'inicio'; (b) crece hasta 'final' dentro de una misma cohorte.
    La cohorte (partidas con estados en las tres etapas) es el control de duracion."""
    y = tabla["y"].to_numpy(dtype=np.uint8)
    p = tabla[f"p_{modelo}"].to_numpy()
    codigos = codigos_partida(tabla["game_id"])
    etapas = tabla["stage"].to_numpy()
    mascara = etapas == "inicio"
    rep = replicar(y, {modelo: p}, codigos, {"inicio": mascara}, n_boot, seed)
    punto = metric_rows_codes(y[mascara], p[mascara], codigos[mascara], None, {}, include_stages=False)[0]
    ic_inicio = intervalo(rep[(modelo, "inicio", "auc")])

    etapas_por_partida = tabla.groupby("game_id")["stage"].nunique()
    cohorte = tabla.loc[tabla["game_id"].isin(etapas_por_partida.index[etapas_por_partida == len(STAGES)])]
    y_c, p_c = cohorte["y"].to_numpy(dtype=np.uint8), cohorte[f"p_{modelo}"].to_numpy()
    codigos_c = codigos_partida(cohorte["game_id"])
    grupos = grupos_etapa(cohorte["stage"].to_numpy())
    rep_c = replicar(y_c, {modelo: p_c}, codigos_c, grupos, n_boot, seed)
    puntos_c = {f["etapa"]: f["auc"] for f in metric_rows_codes(
        y_c, p_c, codigos_c, codigos_etapa(cohorte["stage"]), {})}
    resta = rep_c[(modelo, "final", "auc")] - rep_c[(modelo, "inicio", "auc")]
    ic_delta = intervalo(resta)
    clara, crece = ic_inicio[0] > 0.5, ic_delta[0] > 0
    return {"escenario": escenario, "modelo": modelo, "auc_inicio": punto["auc"],
            "auc_inicio_ic_inf": ic_inicio[0], "auc_inicio_ic_sup": ic_inicio[1],
            "partidas_inicio": punto["n_partidas"], "partidas_cohorte": int(codigos_c.max()) + 1,
            "auc_cohorte_inicio": puntos_c["inicio"], "auc_cohorte_medio": puntos_c["medio"],
            "auc_cohorte_final": puntos_c["final"],
            "delta_final_inicio": puntos_c["final"] - puntos_c["inicio"],
            "delta_ic_inf": ic_delta[0], "delta_ic_sup": ic_delta[1],
            "senal_temprana_clara": clara, "crece_con_duracion_controlada": crece,
            "resultado": "sostenida" if clara and crece else "debilitada"}


def decidir_h2(comparaciones, escenario):
    """H2 se decide con la diferencia de AUC B4 - H2 en la etapa 'inicio'."""
    fila = comparaciones.loc[comparaciones["referencia"].eq("H2") & comparaciones["etapa"].eq("inicio")
                             & comparaciones["metrica"].eq("auc")].iloc[0]
    return {"escenario": escenario, "auc_b4_inicio": float(fila["valor_principal"]),
            "auc_h2_inicio": float(fila["valor_referencia"]), "delta": float(fila["delta"]),
            "ic_inf": float(fila["ic_inf"]), "ic_sup": float(fila["ic_sup"]),
            "resultado": "sostenida" if fila["ic_inf"] > 0 else "refutada"}


def _habilidad(metrica, valor):
    """Habilidad frente a una moneda justa: 0 = azar, 1 = perfecto."""
    if metrica == "auc":
        return 2 * valor - 1
    return 1 - valor / (np.log(2) if metrica == "log_loss" else 0.25)


def alinear_h3(prediccion_a, prediccion_b, modelo="B4"):
    """Mismas filas de las partidas que son test en A y en B, con la prediccion de cada modelo."""
    comunes = set(prediccion_a["game_id"]) & set(prediccion_b["game_id"])
    if not comunes:
        raise ValueError("A y B no comparten partidas de test")
    a = prediccion_a.loc[prediccion_a["game_id"].isin(comunes), ["game_id", "step", "y", f"p_{modelo}"]]
    b = prediccion_b.loc[prediccion_b["game_id"].isin(comunes), ["game_id", "step", "y", f"p_{modelo}"]]
    unidas = a.merge(b, on=["game_id", "step"], suffixes=("_A", "_B"), validate="one_to_one")
    if len(unidas) != len(a) or len(unidas) != len(b) or not unidas["y_A"].equals(unidas["y_B"]):
        raise ValueError("las filas comunes de A y B no coinciden")
    return unidas


def prueba_h3(prediccion_a, prediccion_b, modelo="B4", n_boot=N_BOOT, seed=SEMILLA):
    """H3 en diseno emparejado: mismas partidas, modelo de A contra modelo de B.

    Devuelve (filas por medida, decision). 'A' es el modelo sin brecha temporal y 'B' el que
    solo vio dias anteriores. La regla usa MCB y DSC porque comparten unidades; AUC y las
    perdidas relativas de habilidad se reportan como descripcion (ver el protocolo, seccion 7).
    """
    unidas = alinear_h3(prediccion_a, prediccion_b, modelo)
    y = unidas["y_A"].to_numpy(dtype=np.float64)
    codigos = codigos_partida(unidas["game_id"])
    p_a, p_b = unidas[f"p_{modelo}_A"].to_numpy(), unidas[f"p_{modelo}_B"].to_numpy()
    n_partidas = int(codigos.max()) + 1
    planes = {"A": _PlanMetricas(y, p_a, codigos, n_partidas), "B": _PlanMetricas(y, p_b, codigos, n_partidas)}
    corp = {"A": _PlanCorp(y, p_a, codigos), "B": _PlanCorp(y, p_b, codigos)}

    def medir(multiplicidad):
        return {clave: {**planes[clave].medir(multiplicidad),
                        **corp[clave].medir(multiplicidad)} for clave in planes}

    def derivar(medidas):
        a, b = medidas["A"], medidas["B"]
        salida = {f"delta_{m}": b[m] - a[m] for m in METRICAS}
        for m in METRICAS:
            salida[f"perdida_habilidad_{m}"] = 1 - _habilidad(m, b[m]) / _habilidad(m, a[m])
        for s in ("log_loss", "brier"):
            salida[f"delta_mcb_{s}"] = b[f"{s}_mcb"] - a[f"{s}_mcb"]
            salida[f"delta_dsc_{s}"] = a[f"{s}_dsc"] - b[f"{s}_dsc"]
            salida[f"contraste_{s}"] = salida[f"delta_mcb_{s}"] - salida[f"delta_dsc_{s}"]
        return salida

    puntos = medir(np.ones(n_partidas, dtype=np.int64))
    derivadas = derivar(puntos)
    replicas = {clave: np.empty(n_boot) for clave in derivadas}
    for i, multiplicidad in enumerate(multiplicidades(n_partidas, n_boot, seed)):
        for clave, valor in derivar(medir(multiplicidad)).items():
            replicas[clave][i] = valor
    filas = []
    for clave, valor in derivadas.items():
        inferior, superior = intervalo(replicas[clave])
        filas.append({"medida": clave, "valor": valor, "ic_inf": inferior, "ic_sup": superior})
    filas = pd.DataFrame(filas)
    por_medida = filas.set_index("medida")
    puntajes = ("log_loss", "brier")
    sube_calibracion = all(por_medida.loc[f"delta_mcb_{s}", "ic_inf"] > 0 for s in puntajes)
    contraste_positivo = all(por_medida.loc[f"contraste_{s}", "ic_inf"] > 0 for s in puntajes)
    contraste_negativo = all(por_medida.loc[f"contraste_{s}", "ic_sup"] < 0 for s in puntajes)
    if sube_calibracion and contraste_positivo:
        resultado = "sostenida"
    elif contraste_negativo:
        resultado = "refutada"
    else:
        resultado = "no concluyente"
    decision = {"resultado": resultado, "partidas_comunes": n_partidas, "estados_comunes": len(unidas),
                "metricas_A": puntos["A"], "metricas_B": puntos["B"]}
    return filas, decision


def serie_diaria(tablas, modelo="B4"):
    """Una fila por dia con metricas y CORP del modelo (el 'antes' de H3). Cifras puntuales."""
    tabla = pd.concat(tablas, ignore_index=True)
    filas = []
    for dia, parte in tabla.groupby("day"):
        y = parte["y"].to_numpy(dtype=np.uint8)
        p = parte[f"p_{modelo}"].to_numpy()
        codigos = codigos_partida(parte["game_id"])
        fila = metric_rows_codes(y, p, codigos, None, {"dia": dia}, include_stages=False)[0]
        filas.append({**fila, **descomposicion_corp(y, p, codigos)})
    return pd.DataFrame(filas).drop(columns="etapa")


# ----------------------------------------------------------------------------------------
# Analisis de errores
# ----------------------------------------------------------------------------------------

def tabla_errores(tabla, escenario, modelo="B4", seguro=0.9):
    """Falsos positivos y negativos (umbral 0.5) y errores muy seguros, por etapa.
    Tasas con cada partida con el mismo peso; conteos en estados y partidas."""
    filas = []
    for etapa, mascara in grupos_etapa(tabla["stage"].to_numpy()).items():
        parte = tabla.loc[mascara]
        y = parte["y"].to_numpy()
        p = parte[f"p_{modelo}"].to_numpy()
        pesos = pesos_partida(codigos_partida(parte["game_id"]))
        casos = {"falso_positivo": (p >= 0.5) & (y == 0), "falso_negativo": (p < 0.5) & (y == 1),
                 "seguro_equivocado_alto": (p >= seguro) & (y == 0),
                 "seguro_equivocado_bajo": (p <= 1 - seguro) & (y == 1),
                 "seguro_acertado": ((p >= seguro) & (y == 1)) | ((p <= 1 - seguro) & (y == 0))}
        fila = {"escenario": escenario, "modelo": modelo, "etapa": etapa, "n_estados": len(parte),
                "n_partidas": parte["game_id"].nunique()}
        for nombre, caso in casos.items():
            fila[f"tasa_{nombre}"] = float(pesos[caso].sum() / pesos.sum())
            fila[f"estados_{nombre}"] = int(caso.sum())
            fila[f"partidas_{nombre}"] = int(parte.loc[caso, "game_id"].nunique())
        seguros = casos["seguro_equivocado_alto"] | casos["seguro_equivocado_bajo"] | casos["seguro_acertado"]
        total_seguro = pesos[seguros].sum()
        fila["precision_seguras"] = float(pesos[casos["seguro_acertado"]].sum() / total_seguro) if total_seguro else np.nan
        filas.append(fila)
    return pd.DataFrame(filas)


def perfil_errores(tabla, features, modelo="B4", seguro=0.9, top=15):
    """Que distingue a los estados seguros y equivocados de los seguros y acertados: diferencia
    de medias estandarizada, con cada partida con el mismo peso. Es exploratorio."""
    y = tabla["y"].to_numpy()
    p = tabla[f"p_{modelo}"].to_numpy()
    seguros = (p >= seguro) | (p <= 1 - seguro)
    equivocados = seguros & ((p >= 0.5) != (y == 1))
    acertados = seguros & ~equivocados
    if not equivocados.any() or not acertados.any():
        return pd.DataFrame(columns=["caracteristica", "media_equivocados", "media_acertados", "dif_estandarizada"])
    x = tabla[list(features)].to_numpy(dtype=np.float64)
    pesos = pesos_partida(codigos_partida(tabla["game_id"]))

    def media(mascara):
        return np.average(x[mascara], axis=0, weights=pesos[mascara])

    escala = x[seguros].std(axis=0)
    escala[escala == 0] = 1.0
    m_mal, m_bien = media(equivocados), media(acertados)
    perfil = pd.DataFrame({"caracteristica": list(features), "media_equivocados": m_mal, "media_acertados": m_bien,
                           "dif_estandarizada": (m_mal - m_bien) / escala})
    orden = perfil["dif_estandarizada"].abs().sort_values(ascending=False).index
    return perfil.loc[orden].head(top).reset_index(drop=True)


# ----------------------------------------------------------------------------------------
# SHAP y revision de fuga
# ----------------------------------------------------------------------------------------

def muestra_partidas(game_ids, n, seed=SEMILLA):
    """Partidas completas elegidas al azar; nunca filas sueltas."""
    unicos = np.sort(pd.unique(np.asarray(game_ids)))
    return unicos if len(unicos) <= n else np.sort(np.random.default_rng(seed).choice(unicos, n, replace=False))


def _shap_parte(modelo, x):
    import shap
    return shap.TreeExplainer(modelo).shap_values(x, check_additivity=False)


def valores_shap(modelo, x, n_jobs=8):
    """SHAP por arboles en log-odds. El calculo es de un solo hilo, asi que se reparte en
    procesos. Comprueba la aditividad contra la salida cruda del modelo."""
    import shap
    x = np.asarray(x, dtype=np.float32)
    partes = np.array_split(np.arange(len(x)), max(1, min(n_jobs, len(x))))
    valores = np.vstack(Parallel(n_jobs=n_jobs)(delayed(_shap_parte)(modelo, x[i]) for i in partes))
    base = float(np.ravel(shap.TreeExplainer(modelo).expected_value)[0])
    error = np.abs(valores.sum(axis=1) + base - modelo.decision_function(x)).max()
    if error > 1e-3:
        raise ValueError(f"SHAP no reproduce la salida del modelo: error maximo {error}")
    return valores, base


def importancia_shap(valores, features, etapas, codigos):
    """Media de |SHAP| por caracteristica, global y por etapa, con la familia de cada una."""
    familia = {f: nombre for nombre, columnas in feature_families(list(features)).items() for f in columnas}
    filas = []
    for grupo, mascara in grupos_etapa(etapas).items():
        if not mascara.any():
            continue
        pesos = pesos_partida(codigos_partida(codigos[mascara]))
        media = np.average(np.abs(valores[mascara]), axis=0, weights=pesos)
        for caracteristica, importancia in zip(features, media):
            filas.append({"etapa": grupo, "caracteristica": caracteristica, "familia": familia[caracteristica],
                          "importancia": float(importancia), "fraccion": float(importancia / media.sum())})
    return pd.DataFrame(filas).sort_values(["etapa", "importancia"], ascending=[True, False]).reset_index(drop=True)


def auc_individual(x, y, codigos, features):
    """AUC de cada caracteristica sola, en el sentido que mas le favorezca."""
    n_partidas = int(np.max(codigos)) + 1
    uno = np.ones(n_partidas, dtype=np.int64)
    filas = []
    for i, nombre in enumerate(features):
        auc = _auc_from_plan(_auc_sort_plan(np.asarray(y, dtype=np.float64), x[:, i], codigos), uno)
        filas.append({"caracteristica": nombre, "auc": auc, "auc_mejor_sentido": max(auc, 1 - auc)})
    return pd.DataFrame(filas).sort_values("auc_mejor_sentido", ascending=False).reset_index(drop=True)


def revision_fuga(importancia, individual, features, limite_fraccion=0.5, limite_auc=0.85):
    """Barrera antes de abrir test (protocolo, seccion 6). 'aprobada' es False si algo obliga
    a investigar; la celda de test no corre en ese caso."""
    globales = importancia.loc[importancia["etapa"].eq("global")].sort_values("importancia", ascending=False)
    prohibidas = sorted(set(features) & (set(FORBIDDEN_IN_X) | set(CARD_COLUMNS)))
    primera = globales.iloc[0]
    mejor = individual.iloc[0]
    checks = {"sin_columnas_prohibidas": not prohibidas,
              "ninguna_domina": bool(primera["fraccion"] <= limite_fraccion),
              "ninguna_predice_sola": bool(mejor["auc_mejor_sentido"] < limite_auc)}
    return {**checks, "aprobada": all(checks.values()), "prohibidas": prohibidas,
            "mas_importante": primera["caracteristica"], "fraccion_mas_importante": float(primera["fraccion"]),
            "limite_fraccion": limite_fraccion, "mejor_individual": mejor["caracteristica"],
            "auc_mejor_individual": float(mejor["auc_mejor_sentido"]), "limite_auc": limite_auc,
            "top_10": globales["caracteristica"].head(10).tolist()}


# ----------------------------------------------------------------------------------------
# Curvas de aprendizaje
# ----------------------------------------------------------------------------------------

def _medir_curva(modelo, datos, conjunto, comun):
    return metric_rows_codes(np.asarray(datos.y), modelo.predict_proba(np.asarray(datos.x))[:, 1],
                             np.asarray(datos.group), np.asarray(datos.stage), {**comun, "conjunto": conjunto})


def curva_aprendizaje(data_dir, escenario, features, candidata, modelo_final, seed=SEMILLA, cache_dir="/content",
                      fracciones=(0.25, 0.5, 0.75, 1.0), max_partidas_train=5000):
    """B4 con fracciones anidadas de las partidas de train, medido en val y en train.

    Mismo protocolo que el modelo final (vigilancia, paciencia y tope). La fraccion 1.0 reutiliza
    'modelo_final' (ruta del .joblib) en lugar de reentrenar. La muestra de train es la misma en
    todas las fracciones y pertenece a todos los subconjuntos, para que la brecha sea comparable.
    """
    stream = ScenarioStream(Path(data_dir), escenario, tuple(features))
    partidas = game_counts(stream, "train")["global"].index.to_numpy()
    partidas = np.random.default_rng(seed).permutation(np.sort(partidas))
    filas = []
    with TemporaryDirectory(prefix=f"curva-{escenario}-", dir=cache_dir, ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        (tmp / "muestra").mkdir()
        val = materialize_split(stream, features, "val", tmp)
        tamano_minimo = int(round(min(fracciones) * len(partidas)))
        muestra = materialize_split(stream, features, "train", tmp / "muestra",
                                    games=partidas[:min(max_partidas_train, tamano_minimo)])
        for fraccion in sorted(fracciones):
            n = int(round(fraccion * len(partidas)))
            if fraccion == 1.0:
                item = joblib.load(modelo_final)
            else:
                salida = tmp / f"fraccion_{int(fraccion * 100)}"
                salida.mkdir()
                train = materialize_split(stream, features, "train", salida, games=partidas[:n])
                try:
                    fit_b4_candidates_val(train, val, candidata, seed=seed, max_iter=4000, patience=30,
                                          monitor_fraction=0.15, max_ram_gib=10.0, output_dir=salida,
                                          scenario=escenario, verbose=True)
                finally:
                    train.close()
                item = joblib.load(next(salida.glob("b4_*.joblib")))
            comun = {"escenario": escenario, "fraccion": fraccion, "partidas_train": n,
                     "n_iter": int(item["n_iter_vigilancia"])}
            filas.extend(_medir_curva(item["model"], val, "val", comun))
            filas.extend(_medir_curva(item["model"], muestra, "train", comun))
            del item
    return pd.DataFrame(filas)


def diagnostico_sobreajuste(curva):
    """Brecha train - val del AUC por fraccion y ganancia de val al sumar datos (solo global)."""
    globales = curva.loc[curva["etapa"].eq("global")]
    tabla = globales.pivot(index=["escenario", "fraccion", "partidas_train", "n_iter"],
                           columns="conjunto", values=["auc", "log_loss"])
    tabla.columns = [f"{m}_{c}" for m, c in tabla.columns]
    tabla = tabla.reset_index().sort_values(["escenario", "fraccion"])
    tabla["brecha_auc"] = tabla["auc_train"] - tabla["auc_val"]
    tabla["brecha_log_loss"] = tabla["log_loss_val"] - tabla["log_loss_train"]
    tabla["ganancia_auc_val"] = tabla.groupby("escenario")["auc_val"].diff()
    return tabla.reset_index(drop=True)
