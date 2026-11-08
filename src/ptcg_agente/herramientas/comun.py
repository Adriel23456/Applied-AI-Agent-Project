"""Piezas compartidas por las herramientas: prediccion basica y advertencias.

Las advertencias son obligatorias cuando aplican; el verificador comprueba que esten.
Codigos:
  sin_prediccion        preparacion o estado ya resuelto: el modelo no aplica.
  etapa_inicio          en la etapa de inicio el modelo distingue poco (AUC de test bajo).
  extrema_temprana      probabilidad muy alta o muy baja al inicio: ahi los errores seguros
                        son mas frecuentes.
  fuera_de_dominio      la entrada tiene valores o cartas que el modelo nunca vio.
  poco_frecuente        valores en la cola de la distribucion de entrenamiento.
"""

from ptcg_agente import dominio
from ptcg_agente.lenguaje import frase, porcentaje

UMBRAL_EXTREMO = 0.9


def auc_etapa(modelo, etapa, escenario="A"):
    return modelo.metricas_test.get(escenario, {}).get(etapa, {}).get("auc")


def revision_dominio(modelo, cur):
    hallazgos = dominio.revisar(cur, modelo.perfil, list(modelo.features) + list(dominio.CARTAS))
    return {"dentro_del_dominio": not any(h["severidad"] == "fuera" for h in hallazgos),
            "hallazgos": hallazgos}


def advertencias(modelo, evaluacion, revision):
    """Lista de advertencias {codigo, mensaje} para una evaluacion y su revision de dominio."""
    salida = []
    if evaluacion["estado"] != "modelo":
        motivo = ("la partida esta en preparacion (turno 0)" if evaluacion["estado"] == "preparacion"
                  else "la partida ya esta resuelta (un jugador no tiene premios o Pokemon en juego)")
        salida.append({"codigo": "sin_prediccion",
                       "mensaje": f"No hay probabilidad: {motivo}. El modelo no se entreno con esos estados."})
        return salida
    etapa = modelo.etapa(evaluacion["turno"])
    p = evaluacion["probabilidad"]
    if etapa == "inicio":
        auc = auc_etapa(modelo, "inicio")
        texto_auc = f" (AUC {auc:.3f} en prueba)" if auc is not None else ""
        salida.append({"codigo": "etapa_inicio",
                       "mensaje": "Estimacion de confianza baja: al inicio de la partida el modelo "
                                  f"distingue poco entre posiciones ganadoras y perdedoras{texto_auc}."})
        if p >= UMBRAL_EXTREMO or p <= 1 - UMBRAL_EXTREMO:
            salida.append({"codigo": "extrema_temprana",
                           "mensaje": f"Probabilidad extrema ({porcentaje(p)}) en un turno temprano: "
                                      "en esta etapa las predicciones muy seguras fallan con mas frecuencia."})
    fuera = [h for h in revision["hallazgos"] if h["severidad"] == "fuera"]
    raras = [h for h in revision["hallazgos"] if h["severidad"] == "rara"]
    if fuera:
        detalle = ", ".join(_detalle(h) for h in fuera[:5])
        salida.append({"codigo": "fuera_de_dominio",
                       "mensaje": f"Fuera del dominio de entrenamiento: {detalle}. "
                                  "La probabilidad puede no ser confiable."})
    if raras:
        detalle = ", ".join(_detalle(h) for h in raras[:5])
        salida.append({"codigo": "poco_frecuente",
                       "mensaje": f"Valores poco frecuentes en entrenamiento: {detalle}."})
    return salida


def _detalle(h):
    if h["tipo"] == "carta_no_vista":
        return f"carta activa {h['valor']} nunca vista ({'propia' if h['caracteristica'].startswith('own') else 'del rival'})"
    return f"{frase(h['caracteristica'])} = {h['valor']:g}"


def evaluar(modelo, cur):
    """Probabilidad, estado, etapa y advertencias de una observacion ya validada."""
    ev = modelo.predictor.evaluar(cur)
    revision = revision_dominio(modelo, cur)
    salida = {
        "estado": ev["estado"],
        "turno": ev["turno"],
        "jugador": ev["jugador"],
        "etapa": modelo.etapa(ev["turno"]) if ev["estado"] == "modelo" else None,
        "probabilidad": ev["probabilidad"],
        "probabilidad_texto": porcentaje(ev["probabilidad"]) if ev["probabilidad"] is not None else None,
        "dentro_del_dominio": revision["dentro_del_dominio"],
        "advertencias": advertencias(modelo, ev, revision),
    }
    return salida, revision