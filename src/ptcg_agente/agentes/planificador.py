"""Planificador: de la pregunta del usuario a un plan de herramientas.

Es un agente LLM (Claude) que SOLO decide: no tiene herramientas ni ve el modelo. Devuelve un
plan en JSON con un esquema fijo. Python valida el plan antes de ejecutarlo:
  - solo herramientas que existen y argumentos que esas herramientas aceptan;
  - el archivo es siempre el que dio el usuario (el planificador no puede inventar rutas);
  - como maximo MAX_PASOS pasos.
Si el plan no es valido se le pide uno nuevo con los problemas; si vuelve a fallar se usa un
plan por defecto, que siempre es seguro.
"""

import inspect
import json

from ptcg_agente.herramientas import HERRAMIENTAS

MAX_PASOS = 6

ESQUEMA = {
    "type": "object",
    "properties": {
        "objetivo": {"type": "string"},
        "pasos": {"type": "array", "maxItems": MAX_PASOS, "items": {
            "type": "object",
            "properties": {"herramienta": {"type": "string", "enum": sorted(HERRAMIENTAS)},
                           "argumentos": {"type": "object"},
                           "motivo": {"type": "string"}},
            "required": ["herramienta", "argumentos", "motivo"]}},
    },
    "required": ["objetivo", "pasos"],
}


def parametros(nombre):
    firma = inspect.signature(HERRAMIENTAS[nombre].ejecutar)
    return [p for p in firma.parameters if p != "modelo"]


def catalogo():
    lineas = []
    for n, m in HERRAMIENTAS.items():
        args = [a for a in parametros(n) if a not in ("observacion", "repeticion")]
        lineas.append(f"- {n}({', '.join(args)}): {m.DESCRIPCION}")
    return "\n".join(lineas)


SISTEMA = f"""Eres el PLANIFICADOR de un agente que analiza partidas del Pokemon TCG con un modelo de
probabilidad de victoria. No ejecutas nada: solo decides que herramientas usar, en que orden y
con que argumentos. Otro agente las ejecuta y otro redacta la respuesta.

Herramientas disponibles:
{catalogo()}

Reglas:
- Usa solo esas herramientas y solo esos argumentos. Maximo {MAX_PASOS} pasos.
- Usa exactamente el archivo que da el usuario. No inventes rutas ni observaciones.
- Una repeticion completa se analiza con evaluar_partida; un estado concreto, con 'archivo' y 'paso'.
- Para explicar por que, usa explicar_prediccion en los pasos que importan.
- Si la pregunta es sobre confiabilidad o limites, incluye describir_modelo.
- Responde solo con el JSON pedido."""


def contexto(pregunta, archivo=None, paso=None, descripcion=None):
    partes = [f"Pregunta del usuario: {pregunta}"]
    if archivo:
        partes.append(f"Archivo: {archivo}")
    if paso is not None:
        partes.append(f"Paso indicado por el usuario: {paso}")
    if descripcion:
        partes.append(f"Contenido del archivo: {descripcion}")
    return "\n".join(partes)


def validar(plan, archivo=None):
    """Devuelve (plan_limpio, problemas)."""
    problemas = []
    if not isinstance(plan, dict) or not isinstance(plan.get("pasos"), list) or not plan["pasos"]:
        return None, ["el plan no tiene una lista de pasos"]
    pasos = []
    for i, p in enumerate(plan["pasos"][:MAX_PASOS]):
        nombre = p.get("herramienta") if isinstance(p, dict) else None
        if nombre not in HERRAMIENTAS:
            problemas.append(f"paso {i}: herramienta desconocida {nombre!r}")
            continue
        argumentos = dict(p.get("argumentos") or {})
        # el planificador nunca ve el contenido del archivo: no puede pasar observaciones propias
        for clave in ("observacion", "repeticion"):
            argumentos.pop(clave, None)
        extra = set(argumentos) - set(parametros(nombre))
        if extra:
            problemas.append(f"paso {i}: {nombre} no acepta {sorted(extra)}")
            continue
        if archivo is not None:
            if "archivo" in argumentos or ("archivo" in parametros(nombre) and "estados" not in argumentos):
                argumentos["archivo"] = archivo
            for e in argumentos.get("estados") or []:
                if isinstance(e, dict) and "archivo" in e:
                    e["archivo"] = archivo
        pasos.append({"herramienta": nombre, "argumentos": argumentos, "motivo": p.get("motivo", "")})
    if not pasos:
        problemas.append("ningun paso valido")
        return None, problemas
    return {"objetivo": plan.get("objetivo", ""), "pasos": pasos}, problemas


def por_defecto(archivo=None, paso=None, es_repeticion=False):
    """Plan seguro cuando el planificador no entrega uno valido."""
    if archivo and es_repeticion and paso is None:
        pasos = [{"herramienta": "evaluar_partida", "argumentos": {"archivo": archivo},
                  "motivo": "curva de la partida completa"}]
    elif archivo:
        args = {"archivo": archivo, **({"paso": paso} if paso is not None else {})}
        pasos = [{"herramienta": "estimar_probabilidad", "argumentos": args, "motivo": "probabilidad"},
                 {"herramienta": "explicar_prediccion", "argumentos": dict(args), "motivo": "explicacion"}]
    else:
        pasos = [{"herramienta": "describir_modelo", "argumentos": {}, "motivo": "ficha del modelo"}]
    return {"objetivo": "plan por defecto", "pasos": pasos}


def planificar(llm, pregunta, archivo=None, paso=None, descripcion=None, es_repeticion=False):
    """Devuelve (plan, historial). historial guarda cada intento para el registro."""
    historial = []
    prompt = contexto(pregunta, archivo, paso, descripcion)
    for intento in range(2):
        texto, plan, meta = llm(prompt, SISTEMA, ESQUEMA)
        limpio, problemas = validar(plan, archivo)
        historial.append({"intento": intento + 1, "plan_propuesto": plan, "problemas": problemas,
                          "meta": meta})
        if limpio is not None and not problemas:
            return limpio, historial
        prompt = (contexto(pregunta, archivo, paso, descripcion)
                  + "\n\nTu plan anterior no es valido:\n- " + "\n- ".join(problemas)
                  + f"\nPlan anterior: {json.dumps(plan, ensure_ascii=False)}\nCorrigelo.")
        if limpio is not None and intento == 1:
            return limpio, historial  # usa los pasos validos del segundo intento
    return por_defecto(archivo, paso, es_repeticion), historial