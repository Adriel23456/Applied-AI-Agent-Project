"""Modelo final exportado: de una observacion del juego a probabilidad de victoria (Etapa 3).

Modelo elegido: B4 (HistGradientBoosting, trial 20) ajustado con el train del escenario A.
- B4 es el modelo principal: supera a B0-B3 en los tres escenarios y LightGBM no lo sustituye.
- Se usa el ajuste de A porque su train son partidas al azar de TODOS los dias (la poblacion
  mas amplia y reciente); B solo ve los primeros dias y C deja fuera 33 arquetipos. B y C
  sirven para medir generalizacion, no para desplegar.

Entrada: la observacion que recibe el jugador que va a actuar (observation["current"] del
JSON de Kaggle, o el diccionario completo con la clave "current"). Salida: la probabilidad
de que ESE jugador (yourIndex) gane la partida. Las caracteristicas se calculan con la
misma funcion que genero las tablas de entrenamiento (features.extract_features), en el
mismo orden y con el mismo tipo (float32), asi que no hay una segunda implementacion.

Estados sin prediccion (el modelo no se entreno con ellos):
- "preparacion": turno 0, tablero aun vacio.
- "decidido": algun jugador ya no tiene premios o ya no tiene Pokemon en juego.
Para esos estados probabilidad() devuelve None y evaluar() explica el motivo.

Uso:
    from ptcg_wp.predictor import PredictorVictoria
    predictor = PredictorVictoria.desde_kaggle()       # baja modelo_final/ si falta
    p = predictor.probabilidad(observacion)             # float en [0, 1] o None
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn import __version__ as sklearn_version

from ptcg_wp.features import extract_features, is_decided

MODELO_ORIGEN = "b4/final/escenario_A/b4_auc_CVtrial20.joblib"
METRICAS_ORIGEN = "b4/final/escenario_A/b4_val_finalistas.csv"
MODELO_EXPORTADO = "modelo_final/b4_victoria.joblib"
FICHA_EXPORTADA = "modelo_final/ficha.json"
PERSPECTIVA = "probabilidad de que gane el jugador que actua (yourIndex de la observacion)"


def _current(observacion):
    """Acepta observation["current"] o el diccionario de observacion completo."""
    if not isinstance(observacion, dict):
        raise TypeError("la observacion debe ser un diccionario del JSON del juego")
    cur = observacion.get("current", observacion)
    if not isinstance(cur, dict) or "players" not in cur or "yourIndex" not in cur:
        raise ValueError("la observacion no tiene 'current' con 'players' y 'yourIndex'")
    return cur


def estado_de(observacion):
    """'preparacion', 'decidido' o 'modelo' (el unico tipo de estado con prediccion)."""
    cur = _current(observacion)
    if cur["turn"] == 0:
        return "preparacion"
    if is_decided(cur):
        return "decidido"
    return "modelo"


class PredictorVictoria:
    """Envuelve el modelo final y su lista de caracteristicas."""

    def __init__(self, artefacto):
        self.model = artefacto["model"]
        self.features = list(artefacto["features"])
        self.ficha = {k: v for k, v in artefacto.items() if k != "model"}
        version = artefacto.get("version_sklearn")
        if version and version != sklearn_version:
            raise RuntimeError(f"el modelo se guardo con scikit-learn {version} y hay "
                               f"{sklearn_version}; instala la version de requirements.txt")

    @classmethod
    def cargar(cls, ruta):
        """Carga un .joblib exportado (o el de B4 directamente)."""
        return cls(joblib.load(ruta))

    @classmethod
    def desde_kaggle(cls, raiz=None):
        """Baja modelo_final/ del dataset del equipo (solo si falta) y lo carga."""
        from ptcg_wp import store
        raiz = Path(raiz or store.RESULTADOS_DIR)
        if not store.listo([MODELO_EXPORTADO, FICHA_EXPORTADA], raiz):
            raise RuntimeError("el modelo final no esta en Kaggle: ejecuta la celda de exportacion "
                               "de 05_baseline_B4")
        return cls.cargar(raiz / MODELO_EXPORTADO)

    def caracteristicas(self, observacion):
        """Vector float32 (1, n) en el orden exacto con que se entreno el modelo."""
        fila = extract_features(_current(observacion))
        faltan = [f for f in self.features if f not in fila]
        if faltan:
            raise ValueError(f"la observacion no produce estas caracteristicas: {faltan}")
        return np.asarray([[fila[f] for f in self.features]], dtype=np.float32)

    def evaluar(self, observacion):
        """Diccionario con la probabilidad, el estado y el turno de la observacion."""
        cur = _current(observacion)
        estado = estado_de(cur)
        probabilidad = None
        if estado == "modelo":
            probabilidad = float(self.model.predict_proba(self.caracteristicas(cur))[0, 1])
        return {"probabilidad": probabilidad, "estado": estado, "turno": cur["turn"],
                "jugador": cur["yourIndex"]}

    def probabilidad(self, observacion):
        """Probabilidad de que gane el jugador que actua, o None si no aplica el modelo."""
        return self.evaluar(observacion)["probabilidad"]

    def probabilidades_tabla(self, tabla):
        """Predicciones para filas de una tabla de estados (estados_*.parquet). Sirve para
        verificar el modelo exportado contra las metricas de val sin el JSON crudo."""
        valores = pd.DataFrame(tabla).loc[:, self.features].to_numpy(dtype=np.float32)
        return self.model.predict_proba(valores)[:, 1]


def exportar_modelo_final(raiz_resultados, commit=None):
    """Arma modelo_final/ a partir del B4 de A ya entrenado (no reentrena nada).

    Escribe b4_victoria.joblib (modelo + caracteristicas + ficha) y ficha.json (lo mismo sin
    el modelo, legible). Requiere en raiz_resultados el .joblib y el CSV de val de B4 A.
    Devuelve las rutas relativas escritas.
    """
    raiz = Path(raiz_resultados)
    origen = joblib.load(raiz / MODELO_ORIGEN)
    metricas = pd.read_csv(raiz / METRICAS_ORIGEN)
    from ptcg_wp.store import sha256
    ficha = {
        "modelo": "B4 HistGradientBoostingClassifier (trial 20)",
        "escenario_de_entrenamiento": "A",
        "origen": MODELO_ORIGEN,
        "origen_sha256": sha256(raiz / MODELO_ORIGEN),
        "perspectiva": PERSPECTIVA,
        "estados_sin_prediccion": {"preparacion": "turno 0", "decidido": "sin premios o sin Pokemon en juego"},
        "entrada": "observation['current'] del jugador que actua (o la observacion con 'current')",
        "n_caracteristicas": len(origen["features"]),
        "n_iter": int(origen.get("n_iter_vigilancia", -1)),
        "candidata": origen.get("candidata"),
        "version_sklearn": origen.get("version_sklearn"),
        "metricas_val": metricas.to_dict("records"),
        "nota": "metricas de val; la evaluacion unica en test y la calibracion son de la etapa 05",
        "commit": commit,
    }
    artefacto = {"model": origen["model"], "features": list(origen["features"]), **ficha}
    destino = raiz / MODELO_EXPORTADO
    destino.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefacto, destino)
    (raiz / FICHA_EXPORTADA).write_text(json.dumps(ficha, indent=2, ensure_ascii=False, default=str),
                                        encoding="utf-8")
    return [MODELO_EXPORTADO, FICHA_EXPORTADA]
