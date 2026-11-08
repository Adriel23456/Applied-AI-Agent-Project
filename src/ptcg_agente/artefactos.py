"""Archivos que necesita el agente: bajarlos de Kaggle una vez y verificarlos siempre.

Todo vive en el dataset privado del equipo (configs/datos.yaml), igual que en la Etapa 2.
Localmente se guarda en ARTEFACTOS_DIR (por defecto <repo>/artefactos_agente, fuera de Git)
junto con manifiesto.json, que anota el SHA-256 y el commit de cada archivo segun el indice
de Kaggle en el momento de bajarlo.

Verificacion en cada arranque (sin red):
  1. Cada archivo existe y su SHA-256 coincide con el del manifiesto.
  2. La version de scikit-learn instalada es la misma con que se guardo el modelo (ficha.json).
Si algo falla, el agente no arranca: un modelo distinto al evaluado no debe responder.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sklearn import __version__ as sklearn_version

from ptcg_wp import store
from ptcg_wp.predictor import FICHA_EXPORTADA, MODELO_EXPORTADO

REPO_DIR = Path(__file__).resolve().parents[2]
ARTEFACTOS_DIR = Path(os.environ.get("PTCG_ARTEFACTOS", REPO_DIR / "artefactos_agente"))
MANIFIESTO = "manifiesto.json"

# Perfil del dominio de entrenamiento (lo construye el cuaderno 07 con el train de A)
DOMINIO = "agente/dominio.json"
# Metricas de la evaluacion unica en test (Etapa 2) y veredicto de las hipotesis
METRICAS_TEST = [f"evaluacion_final/test/metricas_{e}.csv" for e in ("A", "B", "C")]
VEREDICTO = "evaluacion_final/veredicto.json"

REQUERIDOS = [MODELO_EXPORTADO, FICHA_EXPORTADA, DOMINIO, *METRICAS_TEST, VEREDICTO]


def probar_kaggle():
    """Intenta bajar el indice UNA vez y, si falla, muestra el mensaje exacto de kaggle.
    Evita los reintentos de 10 minutos de store.leer_indice cuando el problema es local
    (herramienta kaggle ausente, token o permisos), que es lo normal en una PC nueva."""
    import tempfile
    dataset = store.load_dataset_id()
    try:
        with tempfile.TemporaryDirectory(prefix="kaggle-prueba-") as tmp:
            ok, texto = store._bajar_archivo(dataset, store.INDICE, Path(tmp) / store.INDICE)
    except FileNotFoundError as e:
        raise RuntimeError("no se encontro la herramienta 'kaggle': activa .venv e instala "
                           "requirements.txt") from e
    if not ok:
        raise RuntimeError(f"Kaggle no entrego {store.INDICE} de {dataset}. Mensaje de kaggle:\n"
                           f"{texto.strip() or '(vacio)'}")


def preparar(raiz=None, rutas=REQUERIDOS):
    """Baja de Kaggle lo que falte (verificando SHA-256) y escribe el manifiesto.

    Requiere el token de Kaggle configurado (igual que los cuadernos). Solo hace falta la
    primera vez o cuando cambia algun archivo en Kaggle.
    """
    raiz = Path(raiz or ARTEFACTOS_DIR)
    raiz.mkdir(parents=True, exist_ok=True)
    probar_kaggle()
    if not store.listo(list(rutas), raiz):
        raise RuntimeError("faltan archivos del agente en Kaggle; si falta agente/dominio.json, "
                           "ejecuta la celda de dominio del cuaderno 07_agente")
    indice = store.leer_indice()
    manifiesto = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": store.load_dataset_id(),
        "archivos": {r: {"sha256": indice[r]["sha256"], "commit": indice[r].get("commit", ""),
                         "fecha_utc": indice[r].get("fecha_utc", "")} for r in rutas},
    }
    (raiz / MANIFIESTO).write_text(json.dumps(manifiesto, indent=2), encoding="utf-8")
    return verificar(raiz, rutas)


def preparar_ejemplos(raiz=None):
    """Baja (verificando SHA-256) las repeticiones de ejemplo publicadas en Kaggle."""
    from ptcg_agente import ejemplos
    raiz = Path(raiz or ARTEFACTOS_DIR)
    rutas = ejemplos.rutas_publicadas()
    if rutas:
        store.listo(rutas, raiz)
    return [raiz / r for r in rutas]


def preparar_validacion(raiz=None):
    """Baja (verificando SHA-256) los casos de validacion que publico el cuaderno 09."""
    from ptcg_agente.validacion import casos
    raiz = Path(raiz or ARTEFACTOS_DIR)
    rutas = [casos.CASOS, casos.OBSERVACIONES, casos.PARTIDAS]
    if not store.listo(rutas, raiz):
        raise RuntimeError("Kaggle todavia no muestra todos los casos de validacion. Si la parte 1 "
                           "del cuaderno 09 se publico hace poco, espera unos minutos a que Kaggle "
                           "termine de procesar la version nueva y vuelve a ejecutar esta celda; "
                           "si no se ha ejecutado, ejecutala en Colab")
    return raiz


def configurar_kaggle():
    """Token de Kaggle desde la variable KAGGLE_API_TOKEN o desde secrets.txt en la raiz del
    repo (mismo formato de los cuadernos); si no esta, lo pide sin mostrarlo."""
    if not (os.environ.get("KAGGLE_API_TOKEN") or os.environ.get("KAGGLE_KEY")):
        from ptcg_wp.colab import _configure_kaggle, read_secret
        _configure_kaggle(read_secret("KAGGLE_API_TOKEN", path=str(REPO_DIR / "secrets.txt")))


def verificar(raiz=None, rutas=REQUERIDOS):
    """Comprueba SHA-256 contra el manifiesto y la version de scikit-learn contra la ficha.
    Devuelve el manifiesto. Lanza RuntimeError con un mensaje claro si algo no coincide."""
    raiz = Path(raiz or ARTEFACTOS_DIR)
    ruta_manifiesto = raiz / MANIFIESTO
    if not ruta_manifiesto.exists():
        raise RuntimeError(f"no hay {MANIFIESTO} en {raiz}: ejecuta "
                           "'python -m ptcg_agente.artefactos' para bajar el modelo de Kaggle")
    manifiesto = json.loads(ruta_manifiesto.read_text(encoding="utf-8"))
    problemas = []
    for r in rutas:
        esperado = manifiesto["archivos"].get(r, {}).get("sha256")
        archivo = raiz / r
        if not archivo.exists():
            problemas.append(f"falta {r}")
        elif esperado is None:
            problemas.append(f"{r} no esta en el manifiesto")
        elif store.sha256(archivo) != esperado:
            problemas.append(f"{r}: el SHA-256 no coincide con el de Kaggle")
    if problemas:
        raise RuntimeError("artefactos del agente invalidos:\n  - " + "\n  - ".join(problemas))
    ficha = json.loads((raiz / FICHA_EXPORTADA).read_text(encoding="utf-8"))
    version = ficha.get("version_sklearn")
    if version and version != sklearn_version:
        raise RuntimeError(f"el modelo se guardo con scikit-learn {version} y hay {sklearn_version}; "
                           "instala la version de requirements.txt")
    return manifiesto


def main():
    """Uso (desde la raiz del repo): python -m ptcg_agente.artefactos [--raiz CARPETA]
    Lee el token de Kaggle de la variable KAGGLE_API_TOKEN o de secrets.txt en la raiz del repo
    (el mismo formato de los cuadernos); si no lo encuentra, lo pide sin mostrarlo."""
    import argparse
    parser = argparse.ArgumentParser(description="Baja y verifica los archivos del agente")
    parser.add_argument("--raiz", default=None)
    args = parser.parse_args()
    configurar_kaggle()
    manifiesto = preparar(args.raiz)
    print(f"Listo: {len(manifiesto['archivos'])} archivos verificados en "
          f"{Path(args.raiz or ARTEFACTOS_DIR).resolve()}")
    for ruta in preparar_ejemplos(args.raiz):
        print("ejemplo:", ruta)


if __name__ == "__main__":
    main()