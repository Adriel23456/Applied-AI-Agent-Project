"""python -m ptcg_agente.simulador [--archivo PARTIDA.json] [--paso N] [--vacio] [--puerto 8765]"""

import argparse
import sys
import webbrowser
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ptcg_agente.modelo import ModeloAgente
from ptcg_agente.registro import Registro
from ptcg_agente.simulador.servidor import crear, url_de


def main(argv=None):
    p = argparse.ArgumentParser(description="Simulador grafico de la probabilidad de victoria")
    p.add_argument("--archivo", help="repeticion completa de Kaggle (JSON)")
    p.add_argument("--paso", type=int, help="paso inicial de la repeticion")
    p.add_argument("--puerto", type=int, default=8765)
    p.add_argument("--vacio", action="store_true", help="empezar con un estado nuevo, sin partida")
    p.add_argument("--sin-navegador", action="store_true", help="no abrir el navegador")
    args = p.parse_args(argv)
    modelo = ModeloAgente.cargar()
    registro = Registro("simulador", modelo.modelo_sha256, modelo.commit)
    archivo = args.archivo
    if archivo is None and not args.vacio:
        from ptcg_agente.artefactos import ARTEFACTOS_DIR
        ejemplos = sorted((ARTEFACTOS_DIR / "agente" / "ejemplos").glob("partida_*.json"))
        if not ejemplos:
            raise SystemExit("indica --archivo o baja los ejemplos con python -m ptcg_agente.artefactos")
        archivo = str(ejemplos[0])
    servidor = crear(modelo, registro, archivo=archivo, paso=args.paso, puerto=args.puerto)
    if args.vacio:
        servidor.simulador.inicial = servidor.simulador.vacio()
    url = url_de(servidor)
    print(f"Simulador en {url} (Ctrl+C para cerrar)")
    if not args.sin_navegador:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Simulador cerrado")


if __name__ == "__main__":
    main()