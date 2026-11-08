"""Redactor: escribe la respuesta para un usuario no tecnico a partir de resultados ya verificados.

Es un agente LLM (Claude) sin herramientas: solo ve la pregunta y los resultados aprobados por
el verificador, resumidos. No puede consultar el modelo ni inventar datos nuevos; el verificador
revisa su texto despues.

plantilla() es la respuesta de respaldo, armada solo con lo que dicen las herramientas, para
cuando el texto del redactor no aprueba la verificacion tras los reintentos.
"""

import json

from ptcg_agente.lenguaje import porcentaje

SISTEMA = """Eres el REDACTOR de un agente que analiza partidas del Pokemon TCG. Recibes la pregunta
del usuario y los resultados de las herramientas del modelo, ya verificados. Escribe en espanol,
para alguien que no sabe de aprendizaje automatico.

Reglas obligatorias:
- Toda cifra debe salir de los resultados. No calcules cifras nuevas salvo restar una
  probabilidad de 100 %. Escribe las probabilidades como porcentaje con un decimal (62.3 %).
  Para decir que una probabilidad cruzo la mitad escribe "la mitad", no "50 %".
- Explica el por que con las explicaciones recibidas (premios, descartes, mazo, tablero).
- Si hay advertencias, dilas con claridad (por ejemplo, confianza baja al inicio, fuera del dominio).
- Si el modelo no aplica (preparacion o partida resuelta), di que no hay probabilidad y no des porcentajes.
- Nunca menciones ni supongas la mano del rival ni el contenido de los premios.
- No prometas certeza: es una estimacion.
- Se breve y directo: primero la respuesta, luego el por que y al final los limites."""

CAMPOS_FUERA = {"curva", "verificacion", "valor_base_logit", "logit", "suma_shap"}


def resumir(salida):
    """Quita lo que el redactor no necesita (curva paso a paso, valores internos de SHAP)."""
    resumen = {k: v for k, v in salida.items() if k not in CAMPOS_FUERA}
    for clave in ("a_favor", "en_contra"):
        if clave in resumen:
            resumen[clave] = [{k: f[k] for k in ("descripcion", "valor", "efecto_puntos")}
                              for f in resumen[clave]]
    return resumen


def prompt(pregunta, resultados, problemas_previos=None, borrador_previo=None):
    datos = [{"herramienta": r["herramienta"], "argumentos": r["argumentos"],
              "resultado": resumir(r["salida"])} for r in resultados]
    texto = (f"Pregunta del usuario: {pregunta}\n\nResultados verificados:\n"
             f"{json.dumps(datos, ensure_ascii=False, default=str)}")
    if problemas_previos:
        texto += ("\n\nTu borrador anterior NO paso la verificacion por estos motivos:\n- "
                  + "\n- ".join(problemas_previos) + f"\n\nBorrador anterior:\n{borrador_previo}\n"
                  "Escribe una version corregida.")
    return texto


def redactar(llm, pregunta, resultados, problemas_previos=None, borrador_previo=None):
    texto, _, meta = llm(prompt(pregunta, resultados, problemas_previos, borrador_previo), SISTEMA)
    return texto.strip(), meta


def plantilla(resultados):
    """Respuesta minima y segura, sin LLM, construida solo con los resultados."""
    lineas = ["No pude redactar una respuesta que pasara la verificacion; esto es lo que dicen "
              "las herramientas del modelo:"]
    for r in resultados:
        s = r["salida"]
        if r["herramienta"] == "evaluar_partida":
            turnos = ", ".join(f"turno {t['turno']}: {porcentaje(t['p_jugador0'])}" for t in s["turnos"])
            lineas.append(f"- Probabilidad del jugador 0 al cierre de cada turno: {turnos}.")
        elif s.get("texto"):
            lineas.append(f"- {s['texto']}")
        elif s.get("probabilidad_texto"):
            lineas.append(f"- Probabilidad de victoria del jugador que actua: {s['probabilidad_texto']}.")
        elif s.get("resumen"):
            lineas.append(f"- {s['resumen']}")
        for a in s.get("advertencias", []):
            lineas.append(f"- Advertencia: {a['mensaje']}")
    lineas.append("Es una estimacion con informacion publica, no una certeza.")
    return "\n".join(lineas)