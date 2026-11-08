"""Todo lo que el agente necesita del modelo, cargado una sola vez.

ModeloAgente reune:
  - predictor: PredictorVictoria de la Etapa 2 (misma funcion de caracteristicas que el
    entrenamiento, asi que la probabilidad es identica a la del modelo evaluado).
  - explicador SHAP del mismo modelo (se crea al primer uso).
  - ficha del modelo, metricas de test por escenario y etapa, veredicto de H1-H3.
  - perfil del dominio de entrenamiento.
  - SHA-256 del modelo y commit del codigo, para el registro de invocaciones.
"""

import json
import math
import subprocess
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas as pd

from ptcg_agente import artefactos
from ptcg_agente.dominio import etapa
from ptcg_wp.predictor import FICHA_EXPORTADA, MODELO_EXPORTADO, PredictorVictoria

ESCENARIOS = ("A", "B", "C")


def commit_actual():
    """Commit del repositorio donde corre el agente (None si no es un repositorio Git)."""
    try:
        salida = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=artefactos.REPO_DIR,
                                capture_output=True, text=True, timeout=5)
        return salida.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _metricas_b4(ruta):
    tabla = pd.read_csv(ruta)
    if "modelo" in tabla.columns:
        tabla = tabla[tabla["modelo"] == "B4"]
    columnas = [c for c in ("etapa", "auc", "log_loss", "brier", "auc_ic_inf", "auc_ic_sup")
                if c in tabla.columns]
    return {f["etapa"]: {k: float(v) for k, v in f.items() if k != "etapa"}
            for f in tabla[columnas].to_dict("records")}


class ModeloAgente:
    def __init__(self, raiz, verificar=True):
        self.raiz = Path(raiz)
        manifiesto = artefactos.verificar(self.raiz) if verificar else {"archivos": {}}
        self.predictor = PredictorVictoria.cargar(self.raiz / MODELO_EXPORTADO)
        self.ficha = json.loads((self.raiz / FICHA_EXPORTADA).read_text(encoding="utf-8"))
        self.perfil = json.loads((self.raiz / artefactos.DOMINIO).read_text(encoding="utf-8"))
        self.metricas_test = {e: _metricas_b4(self.raiz / r)
                              for e, r in zip(ESCENARIOS, artefactos.METRICAS_TEST)}
        self.veredicto = json.loads((self.raiz / artefactos.VEREDICTO).read_text(encoding="utf-8"))
        self.modelo_sha256 = manifiesto["archivos"].get(MODELO_EXPORTADO, {}).get("sha256")
        self.commit = commit_actual()

    @classmethod
    def cargar(cls, raiz=None, verificar=True):
        return cls(raiz or artefactos.ARTEFACTOS_DIR, verificar=verificar)

    @property
    def features(self):
        return self.predictor.features

    @property
    def cortes(self):
        return self.perfil["cortes_etapa"]

    def etapa(self, turno):
        return etapa(turno, self.cortes)

    @cached_property
    def explicador(self):
        import shap
        return shap.TreeExplainer(self.predictor.model)

    def logit(self, x):
        """Salida cruda del modelo (log-odds) para un vector de caracteristicas."""
        return float(self.predictor.model.decision_function(x)[0])

    def shap(self, x):
        """(valor base, contribuciones) en log-odds. base + suma = logit del modelo."""
        valores = np.asarray(self.explicador.shap_values(x, check_additivity=False))
        base = float(np.ravel(self.explicador.expected_value)[0])
        return base, valores.reshape(-1)[: x.shape[1]]


def sigmoide(z):
    return 1.0 / (1.0 + math.exp(-z))