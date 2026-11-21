"""estimar_probabilidad: observacion publica -> probabilidad de victoria del jugador que actua.

Devuelve tambien la etapa de la partida, si la entrada esta dentro del dominio de
entrenamiento y las advertencias que el usuario debe ver. En preparacion y en estados ya
resueltos la probabilidad es None (el modelo no se entreno con ellos).
"""

from ptcg_agente.entradas import resolver
from ptcg_agente.herramientas.comun import auc_etapa, evaluar

NOMBRE = "estimar_probabilidad"
DESCRIPCION = ("Probabilidad de que gane el jugador que actua, a partir de su observacion publica. "
               "Incluye etapa de la partida, revision de dominio y advertencias obligatorias.")


def ejecutar(modelo, observacion=None, archivo=None, paso=None):
    cur, origen = resolver(observacion, archivo, paso)
    salida, _ = evaluar(modelo, cur)
    if salida["etapa"]:
        salida["auc_test_etapa"] = auc_etapa(modelo, salida["etapa"])
    return {"ok": True, "origen": origen, **salida}