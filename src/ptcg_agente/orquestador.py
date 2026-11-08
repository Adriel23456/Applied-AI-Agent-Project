"""Orquestador multiagente: planificador -> ejecutor -> verificador -> redactor -> verificador.

  planificador  Claude, aislado y sin herramientas: convierte la pregunta en un plan JSON.
  ejecutor      Python: corre el plan sobre el modelo final (herramientas/).
  verificador   Python, deterministico: revisa cada resultado y luego el texto final.
  redactor      Claude, aislado y sin herramientas: escribe la respuesta con los resultados aprobados.

Si el texto del redactor no aprueba, se le devuelve con los problemas (hasta 'intentos' veces).
Si sigue sin aprobar, la respuesta es la plantilla deterministica. Ninguna cifra llega al
usuario sin pasar por el verificador. Cada etapa queda en el registro JSONL con su agente.

Uso desde la raiz del repositorio (con el entorno .venv activo y Claude Code iniciado):
    python -m ptcg_agente.orquestador "¿Quien va ganando y por que?" --archivo partida.json --paso 120
(desde la raiz: PYTHONPATH=src, o 'pip install -e .' si se instala el paquete)
"""

import argparse
import json
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ptcg_agente.agentes import ejecutor, planificador, redactor
from ptcg_agente.agentes.llm import ErrorLLM, llamar_claude
from ptcg_agente.agentes.verificador import verificar_texto
from ptcg_agente.entradas import EntradaInvalida, es_repeticion, leer_json
from ptcg_agente.modelo import ModeloAgente
from ptcg_agente.registro import Registro


def describir_archivo(archivo):
    """Descripcion corta del archivo para el planificador (no le pasa el contenido)."""
    if not archivo:
        return None, False
    try:
        datos = leer_json(archivo)
    except EntradaInvalida as e:
        return f"no se pudo leer: {e}", False
    if es_repeticion(datos):
        return f"repeticion completa de Kaggle con {len(datos['steps'])} pasos (0 a {len(datos['steps']) - 1})", True
    return "observacion de un solo estado (observation['current'])", False


def _anotar(registro, etapa, entrada, salida, inicio, agente):
    if registro is not None:
        registro.anotar(etapa, entrada, salida, 1000 * (time.perf_counter() - inicio), agente)


def consultar(pregunta, archivo=None, paso=None, modelo=None, llm=llamar_claude, registro=None,
              intentos=2):
    """Responde una pregunta con los cuatro agentes. Devuelve un dict con todo el recorrido."""
    modelo = modelo or ModeloAgente.cargar()
    if registro is None:
        registro = Registro("orquestador", modelo.modelo_sha256, modelo.commit)
    if archivo:
        archivo = str(Path(archivo).expanduser().resolve())
    descripcion, repeticion = describir_archivo(archivo)

    # 1. Planificador
    inicio = time.perf_counter()
    try:
        plan, historial = planificador.planificar(llm, pregunta, archivo, paso, descripcion, repeticion)
        fuente_plan = "planificador" if historial and not historial[-1]["problemas"] else "por_defecto"
    except ErrorLLM as e:
        plan, historial = planificador.por_defecto(archivo, paso, repeticion), [{"error": str(e)}]
        fuente_plan = "por_defecto"
    _anotar(registro, "planificar", {"pregunta": pregunta, "archivo": archivo, "paso": paso},
            {"plan": plan, "fuente": fuente_plan, "intentos": historial}, inicio, "planificador")

    # 2. Ejecutor (cada herramienta ya pasa por el verificador de resultados)
    resultados = ejecutor.ejecutar(plan, modelo, registro)
    aprobados = ejecutor.utilizables(resultados)
    if not aprobados and fuente_plan == "planificador":
        # el plan era valido en forma pero ninguna herramienta dio un resultado usable
        plan, fuente_plan = planificador.por_defecto(archivo, paso, repeticion), "por_defecto"
        resultados = ejecutor.ejecutar(plan, modelo, registro)
        aprobados = ejecutor.utilizables(resultados)
    salidas = [r["salida"] for r in aprobados]

    # 3. Redactor + verificador de texto
    texto, verificacion, problemas, borrador = None, None, None, None
    rondas = []
    fuente = "plantilla"
    if aprobados:
        for ronda in range(intentos):
            inicio = time.perf_counter()
            try:
                borrador, meta = redactor.redactar(llm, pregunta, aprobados, problemas, borrador)
            except ErrorLLM as e:
                _anotar(registro, "redactar", {"ronda": ronda + 1}, {"error": str(e)}, inicio, "redactor")
                break
            _anotar(registro, "redactar", {"ronda": ronda + 1, "problemas_previos": problemas},
                    {"texto": borrador, "meta": meta}, inicio, "redactor")
            inicio = time.perf_counter()
            verificacion = verificar_texto(borrador, salidas)
            _anotar(registro, "verificar_respuesta", {"texto": borrador}, verificacion, inicio, "verificador")
            rondas.append({"ronda": ronda + 1, "texto": borrador, "verificacion": verificacion})
            if verificacion["aprobado"]:
                texto, fuente = borrador, "redactor"
                break
            problemas = verificacion["problemas"]

    if texto is None:
        if aprobados:
            texto = redactor.plantilla(aprobados)
        else:
            errores = [r["salida"].get("error") or "resultado no aprobado" for r in resultados]
            texto = ("No pude obtener un resultado valido del modelo para esta consulta: "
                     + "; ".join(str(e) for e in errores))
        verificacion = verificar_texto(texto, salidas)
        _anotar(registro, "verificar_respuesta", {"texto": texto, "fuente": "plantilla"}, verificacion,
                time.perf_counter(), "verificador")

    return {"pregunta": pregunta, "archivo": archivo, "paso": paso, "plan": plan,
            "fuente_plan": fuente_plan, "resultados": resultados, "rondas_redactor": rondas,
            "respuesta": texto, "fuente_respuesta": fuente, "verificacion": verificacion,
            "sesion": registro.sesion, "registro": str(registro.archivo)}


def main(argv=None):
    p = argparse.ArgumentParser(description="Consulta multiagente sobre una partida del Pokemon TCG.")
    p.add_argument("pregunta")
    p.add_argument("--archivo", help="JSON de observacion o repeticion completa de Kaggle")
    p.add_argument("--paso", type=int, help="paso de la repeticion (si el archivo es una repeticion)")
    p.add_argument("--modelo-claude", help="modelo de Claude para planificador y redactor (opcional)")
    p.add_argument("--json", action="store_true", help="imprime el recorrido completo en JSON")
    args = p.parse_args(argv)

    llm = llamar_claude
    if args.modelo_claude:
        def llm(prompt, sistema, esquema=None):
            return llamar_claude(prompt, sistema, esquema, modelo=args.modelo_claude)

    r = consultar(args.pregunta, args.archivo, args.paso, llm=llm)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
        return
    print("PLAN (" + r["fuente_plan"] + "):")
    for i, s in enumerate(r["plan"]["pasos"]):
        print(f"  {i + 1}. {s['herramienta']} {s['argumentos']} - {s['motivo']}")
    print(f"\nRESPUESTA ({r['fuente_respuesta']}, rondas del redactor: {len(r['rondas_redactor'])}):\n")
    print(r["respuesta"])
    v = r["verificacion"]
    print(f"\nVERIFICACION: {'aprobada' if v['aprobado'] else 'NO aprobada'}, "
          f"cifras revisadas: {v['cifras_revisadas']}" + (f", problemas: {v['problemas']}" if v["problemas"] else ""))
    print(f"Registro: {r['registro']} (sesion {r['sesion']})")


if __name__ == "__main__":
    main()