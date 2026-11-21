"""comparar_estados: probabilidad de dos o mas estados alternativos de la misma posicion.

Uso tipico: el estado despues de la jugada 1 contra el estado despues de la jugada 2. El
modelo no conoce las reglas del juego: solo evalua cada estado ya formado. Las diferencias se
dan contra el primer estado, que sirve de referencia.
"""

from ptcg_agente.entradas import EntradaInvalida, resolver
from ptcg_agente.herramientas.comun import evaluar
from ptcg_agente.lenguaje import porcentaje

NOMBRE = "comparar_estados"
DESCRIPCION = ("Compara la probabilidad de victoria de varios estados alternativos (por ejemplo, "
               "tras jugadas distintas) y ordena cual favorece mas al jugador que actua.")

MAX_ESTADOS = 8


def ejecutar(modelo, estados):
    if not isinstance(estados, list) or not 2 <= len(estados) <= MAX_ESTADOS:
        raise EntradaInvalida(f"'estados' debe ser una lista de 2 a {MAX_ESTADOS} elementos")
    filas, jugadores = [], set()
    for k, e in enumerate(estados):
        if not isinstance(e, dict):
            raise EntradaInvalida(f"el estado {k} debe ser un objeto con 'observacion' o 'archivo'")
        cur, origen = resolver(e.get("observacion"), e.get("archivo"), e.get("paso"))
        salida, _ = evaluar(modelo, cur)
        jugadores.add(salida["jugador"])
        filas.append({"etiqueta": e.get("etiqueta") or f"estado {k + 1}", "origen": origen, **salida})
    if len(jugadores) > 1:
        raise EntradaInvalida("los estados son de jugadores distintos: compara solo estados del "
                              "mismo jugador que actua")
    referencia = filas[0]["probabilidad"]
    for f in filas:
        f["diferencia_vs_primero"] = (None if f["probabilidad"] is None or referencia is None
                                      else round(f["probabilidad"] - referencia, 4))
    validos = [f for f in filas if f["probabilidad"] is not None]
    mejor = max(validos, key=lambda f: f["probabilidad"]) if validos else None
    advertencias = [{"estado": f["etiqueta"], **a} for f in filas for a in f["advertencias"]]
    return {"ok": True, "jugador": jugadores.pop(), "estados": filas,
            "mejor": mejor["etiqueta"] if mejor else None,
            "mejor_texto": porcentaje(mejor["probabilidad"]) if mejor else None,
            "advertencias": advertencias}