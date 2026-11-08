"""abrir_simulador: abre el simulador grafico con un estado o una partida.

No es una herramienta de analisis: no esta en el catalogo del planificador del orquestador
(abrir un navegador no responde una pregunta). La usa Claude a traves del servidor MCP cuando
el usuario quiere ver o manipular un estado. El simulador queda corriendo mientras corra el
proceso que lo abrio (el servidor MCP o la terminal).
"""

import webbrowser

from ptcg_agente.artefactos import ARTEFACTOS_DIR
from ptcg_agente.entradas import EntradaInvalida, es_repeticion, leer_json, validar_current
from ptcg_agente.simulador.servidor import lanzar

NOMBRE = "abrir_simulador"
DESCRIPCION = ("Abre en el navegador el simulador grafico: muestra el tablero de ambos jugadores, deja "
               "editar premios, PV, banca, mazo, descarte y energias, y actualiza la probabilidad, las "
               "contribuciones SHAP y las advertencias en tiempo real. Con una repeticion completa "
               "tambien permite recorrerla paso a paso sobre su curva de probabilidad. Con vacio=true "
               "abre un estado nuevo, sin partida, para armarlo desde cero.")


def ejecutar(modelo, observacion=None, archivo=None, paso=None, vacio=False, registro=None, abrir=True):
    if vacio:
        servidor, url = lanzar(modelo, registro, abrir=False)
        servidor.simulador.inicial = servidor.simulador.vacio()
        if abrir:
            webbrowser.open(url)
        return {"ok": True, "url": url, "archivo": None, "paso": None,
                "mensaje": f"Simulador abierto en {url} con un estado nuevo, sin partida."}
    if observacion is not None and archivo is not None:
        raise EntradaInvalida("indica 'observacion' o 'archivo', no los dos")
    if observacion is None and archivo is None:
        ejemplos = sorted((ARTEFACTOS_DIR / "agente" / "ejemplos").glob("partida_*.json"))
        if not ejemplos:
            raise EntradaInvalida("indica 'archivo' u 'observacion' (no hay repeticiones de ejemplo)")
        archivo = str(ejemplos[0])
    if archivo is not None and not es_repeticion(leer_json(archivo)):
        observacion, archivo = leer_json(archivo), None
    if observacion is not None:
        observacion = validar_current(observacion)
    _, url = lanzar(modelo, registro, observacion=observacion, archivo=archivo, paso=paso, abrir=abrir)
    return {"ok": True, "url": url, "archivo": archivo, "paso": paso,
            "mensaje": f"Simulador abierto en {url}. Sigue activo mientras este abierto el agente."}