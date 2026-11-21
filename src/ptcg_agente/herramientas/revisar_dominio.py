"""revisar_dominio: dice si una entrada esta dentro de lo que el modelo vio al entrenar.

No calcula la probabilidad. Detecta:
  - formato invalido (la herramienta devuelve ok=False con el motivo),
  - preparacion o estado ya resuelto (el modelo no aplica),
  - valores fuera del rango de entrenamiento o poco frecuentes,
  - cartas activas que nunca aparecieron en entrenamiento.
"""

from ptcg_agente.entradas import resolver
from ptcg_wp.predictor import estado_de
from ptcg_agente.herramientas.comun import revision_dominio, _detalle

NOMBRE = "revisar_dominio"
DESCRIPCION = ("Revisa si una observacion esta dentro del dominio de entrenamiento: formato, "
               "preparacion o estado resuelto, valores fuera de rango y cartas nunca vistas.")


def ejecutar(modelo, observacion=None, archivo=None, paso=None):
    cur, origen = resolver(observacion, archivo, paso)
    estado = estado_de(cur)
    revision = revision_dominio(modelo, cur)
    aplica = estado == "modelo"
    if not aplica:
        resumen = f"El modelo no aplica a este estado ({estado})."
    elif revision["dentro_del_dominio"] and not revision["hallazgos"]:
        resumen = "Dentro del dominio de entrenamiento."
    elif revision["dentro_del_dominio"]:
        resumen = "Dentro del dominio, con valores poco frecuentes: " + ", ".join(
            _detalle(h) for h in revision["hallazgos"][:5]) + "."
    else:
        resumen = "Fuera del dominio de entrenamiento: " + ", ".join(
            _detalle(h) for h in revision["hallazgos"] if h["severidad"] == "fuera") + "."
    return {"ok": True, "origen": origen, "estado": estado, "turno": cur["turn"],
            "modelo_aplica": aplica, **revision, "resumen": resumen}