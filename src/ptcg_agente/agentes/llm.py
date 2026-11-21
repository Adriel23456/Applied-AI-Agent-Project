"""Llamada a Claude para los agentes que razonan (planificador y redactor).

Se usa Claude Code sin interfaz (`claude -p`), que trabaja con la sesion de la membresia del
equipo: no hace falta clave de API. Cada llamada es aislada:
  - sin herramientas (--tools ""): el planificador y el redactor no pueden ejecutar nada;
  - sin servidores MCP (--strict-mcp-config): no ven el modelo directamente;
  - sin guardar la sesion (--no-session-persistence).
El planificador pide salida estructurada con un esquema JSON (--json-schema).

Toda funcion LLM del paquete tiene la misma firma:
    llm(prompt, sistema, esquema=None) -> (texto, estructurado, meta)
Asi el orquestador no depende de como se llama a Claude.
"""

import json
import shutil
import subprocess


class ErrorLLM(RuntimeError):
    """Claude no respondio o respondio con un error."""


def _ejecutable():
    ruta = shutil.which("claude")
    if ruta is None:
        raise ErrorLLM("no se encontro 'claude': instala Claude Code y abre una terminal nueva "
                       "(docx/05AmbienteDeDesarrollo/GuiaDelAgente.md, seccion 3.1)")
    return ruta


def llamar_claude(prompt, sistema, esquema=None, modelo=None, timeout=300):
    """Una llamada aislada a Claude Code. El prompt va por stdin (sin limite de linea de comandos)."""
    comando = [_ejecutable(), "-p", "--output-format", "json", "--system-prompt", sistema,
               "--tools", "", "--strict-mcp-config", "--no-session-persistence",
               "--disable-slash-commands"]
    if esquema is not None:
        comando += ["--json-schema", json.dumps(esquema)]
    if modelo:
        comando += ["--model", modelo]
    try:
        res = subprocess.run(comando, input=prompt, capture_output=True, text=True,
                             encoding="utf-8", timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise ErrorLLM(f"Claude no respondio en {timeout} s") from e
    try:
        datos = json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise ErrorLLM(f"respuesta de Claude ilegible (codigo {res.returncode}): "
                       f"{(res.stdout or res.stderr)[-500:]}") from e
    if datos.get("is_error") or res.returncode != 0:
        raise ErrorLLM(f"Claude respondio con error: {str(datos.get('result'))[-500:]}")
    texto = datos.get("result") or ""
    estructurado = datos.get("structured_output")
    if esquema is not None and estructurado is None:
        estructurado = _json_en_texto(texto)
    meta = {k: datos.get(k) for k in ("duration_ms", "num_turns", "total_cost_usd", "session_id")}
    meta["modelo"] = next(iter(datos.get("modelUsage") or {}), modelo)
    return texto, estructurado, meta


def _json_en_texto(texto):
    """Recupera un objeto JSON de un texto (con o sin bloque ```json)."""
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio < 0 or fin <= inicio:
        return None
    try:
        return json.loads(texto[inicio:fin + 1])
    except json.JSONDecodeError:
        return None