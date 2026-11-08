"""Servidor MCP: expone las herramientas del modelo a Claude Desktop y a Claude Code.

Reparto de roles cuando se usa desde Claude:
  - Planificador y redactor: Claude (el LLM decide que herramientas llamar y redacta).
  - Ejecutor: este servidor (corre el modelo y devuelve resultados estructurados).
  - Verificador: este servidor. Revisa cada resultado antes de devolverlo y ofrece
    verificar_respuesta para revisar el borrador final; Claude debe llamarla antes de responder.

Ejecucion desde la raiz del repositorio:
    python src/ptcg_agente/servidor_mcp.py
Claude Code lo levanta solo con el archivo .mcp.json de la raiz del repositorio; Claude Desktop,
con la configuracion de docx/05AmbienteDeDesarrollo/GuiaDelAgente.md.
"""

import sys
from collections import deque
from pathlib import Path

# Permite lanzarlo como archivo (python src/ptcg_agente/servidor_mcp.py), que es lo que usan
# .mcp.json y Claude Desktop: agrega src/ al path si el paquete no es importable.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp.server.mcpserver import MCPServer

from ptcg_agente import herramientas as hz
from ptcg_agente.entradas import EntradaInvalida
from ptcg_agente.herramientas import abrir_simulador as abrir_simulador_hz
from ptcg_agente.agentes.verificador import verificar_texto
from ptcg_agente.modelo import ModeloAgente
from ptcg_agente.registro import Registro

INSTRUCCIONES = """Herramientas del proyecto PTCG Win Probability (Pokemon TCG, Track A, TEC IC-6200).
El modelo estima la probabilidad de que gane el jugador que actua, a partir de su observacion publica.

Sigue este flujo en cada consulta:
1. PLANIFICA: decide que herramientas necesitas (estimar_probabilidad, explicar_prediccion,
   evaluar_partida, comparar_estados, revisar_dominio, describir_modelo).
2. EJECUTA: llamalas. Cada resultado trae "verificacion"; si no esta aprobado, no uses esas cifras.
3. REDACTA para un usuario no tecnico: probabilidad, por que (en premios, descartes, mazo y
   tablero) y sus limites. Toda cifra debe salir de una herramienta. Menciona las advertencias.
4. VERIFICA: llama a verificar_respuesta con tu borrador. Si no aprueba, corrige y vuelve a
   verificar. Si no logras aprobarlo, di que no puedes afirmar mas de lo que dicen las herramientas.
Si el usuario quiere ver el tablero, manipular un estado o recorrer una partida, usa abrir_simulador
y dale la direccion que devuelve.
Nunca pidas ni supongas la mano del rival ni el contenido de los premios. No prometas certeza."""

servidor = MCPServer(name="ptcg-victoria", instructions=INSTRUCCIONES)
_estado = {"modelo": None, "registro": None, "salidas": deque(maxlen=20)}


def _modelo():
    if _estado["modelo"] is None:
        modelo = ModeloAgente.cargar()
        _estado["modelo"] = modelo
        _estado["registro"] = Registro("claude-mcp", modelo.modelo_sha256, modelo.commit)
    return _estado["modelo"]


def _llamar(nombre, **argumentos):
    try:
        modelo = _modelo()
    except Exception as e:  # el modelo no esta listo: se explica en vez de caer
        return {"ok": False, "error": f"el modelo no esta disponible: {e}"}
    salida = hz.llamar(modelo, nombre, argumentos, _estado["registro"], agente="ejecutor")
    if salida.get("ok"):
        _estado["salidas"].append(salida)
    return salida


@servidor.tool(description=hz.estimar_probabilidad.DESCRIPCION)
def estimar_probabilidad(observacion: dict | None = None, archivo: str | None = None,
                         paso: int | None = None) -> dict:
    """observacion: observation['current'] del jugador que actua. archivo: ruta a un JSON de
    observacion o de repeticion completa (con 'paso')."""
    return _llamar("estimar_probabilidad", observacion=observacion, archivo=archivo, paso=paso)


@servidor.tool(description=hz.explicar_prediccion.DESCRIPCION)
def explicar_prediccion(observacion: dict | None = None, archivo: str | None = None,
                        paso: int | None = None, top: int = 5) -> dict:
    return _llamar("explicar_prediccion", observacion=observacion, archivo=archivo, paso=paso, top=top)


@servidor.tool(description=hz.evaluar_partida.DESCRIPCION)
def evaluar_partida(archivo: str | None = None, repeticion: dict | None = None) -> dict:
    """archivo: ruta a una repeticion completa de Kaggle (JSON con 'steps')."""
    salida = _llamar("evaluar_partida", archivo=archivo, repeticion=repeticion)
    return salida


@servidor.tool(description=hz.comparar_estados.DESCRIPCION)
def comparar_estados(estados: list[dict]) -> dict:
    """estados: lista de {"etiqueta", "observacion" | "archivo", "paso"}."""
    return _llamar("comparar_estados", estados=estados)


@servidor.tool(description=hz.revisar_dominio.DESCRIPCION)
def revisar_dominio(observacion: dict | None = None, archivo: str | None = None,
                    paso: int | None = None) -> dict:
    return _llamar("revisar_dominio", observacion=observacion, archivo=archivo, paso=paso)


@servidor.tool(description=hz.describir_modelo.DESCRIPCION)
def describir_modelo() -> dict:
    return _llamar("describir_modelo")


@servidor.tool(description=abrir_simulador_hz.DESCRIPCION)
def abrir_simulador(observacion: dict | None = None, archivo: str | None = None,
                    paso: int | None = None, vacio: bool = False) -> dict:
    """archivo: repeticion completa (con 'paso' opcional) u observacion. vacio=true: estado nuevo
    sin partida. Sin argumentos abre el primer ejemplo."""
    try:
        modelo = _modelo()
        salida = abrir_simulador_hz.ejecutar(modelo, observacion, archivo, paso, vacio=vacio,
                                             registro=_estado["registro"])
    except EntradaInvalida as e:
        salida = {"ok": False, "error": str(e)}
    except Exception as e:  # el modelo no esta listo u otro problema local: se explica en vez de caer
        salida = {"ok": False, "error": f"no se pudo abrir el simulador: {e}"}
    if _estado["registro"] is not None:
        _estado["registro"].anotar("abrir_simulador", {"archivo": archivo, "paso": paso}, salida, 0.0,
                                   agente="ejecutor")
    return salida


@servidor.tool(description="Verifica el borrador de respuesta contra los resultados de las herramientas "
                           "de esta sesion: cifras trazables, advertencias mencionadas y sin promesas de certeza.")
def verificar_respuesta(texto: str) -> dict:
    salidas = list(_estado["salidas"])
    resultado = verificar_texto(texto, salidas)
    if _estado["registro"] is not None:
        _estado["registro"].anotar("verificar_respuesta", {"texto": texto}, resultado, 0.0,
                                   agente="verificador")
    return resultado


@servidor.prompt(description="Consulta completa sobre un estado de partida, siguiendo el flujo multiagente.")
def consulta_ptcg(archivo: str, pregunta: str = "¿Quien va ganando y por que?") -> str:
    return (f"{pregunta}\nArchivo: {archivo}\n"
            "Planifica las herramientas, ejecutalas, redacta para un usuario no tecnico y verifica "
            "tu borrador con verificar_respuesta antes de responder.")


def main():
    servidor.run()


if __name__ == "__main__":
    main()