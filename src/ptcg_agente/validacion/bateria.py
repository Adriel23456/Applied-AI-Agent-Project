"""Corre todo el nivel N1 del protocolo y devuelve tres tablas:
  resultados  una fila por caso del protocolo (aprobado True, False o None = solo registro)
  detalle     una fila por estado real evaluado (normales, poblaciones y errores)
  latencias   una fila por llamada a una herramienta
"""

import pandas as pd

from ptcg_agente.validacion import entradas, errores, limite, normales, poblaciones, sinteticos
from ptcg_agente.validacion.comun import Bateria

GRUPOS = (normales, limite, entradas, poblaciones, sinteticos, errores)
RESULTADOS_N1 = "agente/validacion/resultados_n1.csv"
DETALLE_N1 = "agente/validacion/detalle_n1.csv"
LATENCIAS_N1 = "agente/validacion/latencias_n1.csv"


def correr_n1(modelo, datos, registro=None):
    bat = Bateria(modelo, registro)
    for grupo in GRUPOS:
        grupo.correr(bat, datos)
    excepciones = sum(r["excepcion"] for r in bat.resultados)
    bat.resultados.append({"caso": "R-01", "grupo": "robustez", "descripcion": "toda la bateria N1",
                           "esperado": "0 excepciones sin controlar",
                           "obtenido": f"{excepciones} excepciones en {len(bat.resultados)} casos",
                           "aprobado": excepciones == 0, "excepcion": False, "duracion_ms": 0.0})
    return pd.DataFrame(bat.resultados), pd.DataFrame(bat.detalle), pd.DataFrame(bat.latencias)