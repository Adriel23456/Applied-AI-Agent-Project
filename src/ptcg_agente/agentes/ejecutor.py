"""Ejecutor: corre el plan, herramienta por herramienta, sobre el modelo final.

No usa un LLM. Cada llamada pasa por herramientas.llamar, que valida la entrada, ejecuta el
modelo, aplica el verificador al resultado y lo anota en el registro.
"""

from ptcg_agente import herramientas as hz


def ejecutar(plan, modelo, registro=None):
    resultados = []
    for i, paso in enumerate(plan["pasos"]):
        salida = hz.llamar(modelo, paso["herramienta"], paso["argumentos"], registro, agente="ejecutor")
        resultados.append({"paso": i, "herramienta": paso["herramienta"],
                           "argumentos": paso["argumentos"], "salida": salida})
    return resultados


def utilizables(resultados):
    """Salidas correctas y aprobadas por el verificador: las unicas que el redactor puede usar."""
    return [r for r in resultados if r["salida"].get("ok") and r["salida"]["verificacion"]["aprobado"]]