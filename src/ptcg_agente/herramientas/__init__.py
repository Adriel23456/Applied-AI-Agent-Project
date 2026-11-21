"""Herramientas del agente: una por archivo, independientes de cualquier LLM.

Todas se llaman igual: llamar(modelo, nombre, argumentos, registro). Esa funcion:
  1. ejecuta la herramienta;
  2. convierte una entrada invalida en {"ok": False, "error": ...} (el agente no se cae);
  3. pasa el resultado por el verificador y le agrega "verificacion";
  4. anota la llamada en el registro JSONL.
"""

import time

from ptcg_agente.agentes.verificador import verificar_salida
from ptcg_agente.entradas import EntradaInvalida
from ptcg_agente.herramientas import (comparar_estados, describir_modelo, estimar_probabilidad,
                                      evaluar_partida, explicar_prediccion, revisar_dominio)

MODULOS = [estimar_probabilidad, explicar_prediccion, evaluar_partida, comparar_estados,
           revisar_dominio, describir_modelo]
HERRAMIENTAS = {m.NOMBRE: m for m in MODULOS}


def llamar(modelo, nombre, argumentos=None, registro=None, agente=None):
    if nombre not in HERRAMIENTAS:
        raise KeyError(f"herramienta desconocida: {nombre}")
    argumentos = {k: v for k, v in (argumentos or {}).items() if v is not None}
    inicio = time.perf_counter()
    try:
        salida = HERRAMIENTAS[nombre].ejecutar(modelo, **argumentos)
    except EntradaInvalida as e:
        salida = {"ok": False, "error": str(e)}
    except TypeError as e:
        salida = {"ok": False, "error": f"argumentos invalidos para {nombre}: {e}"}
    salida["verificacion"] = verificar_salida(nombre, salida)
    if registro is not None:
        registro.anotar(nombre, argumentos, salida, 1000 * (time.perf_counter() - inicio), agente)
    return salida