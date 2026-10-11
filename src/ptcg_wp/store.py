"""Almacen de las tablas procesadas en un dataset PRIVADO de Kaggle.

El repo guarda la receta (ingest.py + dias.yaml); este dataset guarda el resultado
para no repetir ~12 minutos de ingesta por dia en cada servidor nuevo de Colab.
  publicar : sube los Parquet de una carpeta como nueva version del dataset
  bajar    : descarga los Parquet del dataset a una carpeta
"""

import argparse
import json
import subprocess
from pathlib import Path

import yaml


def load_dataset_id(config_path):
    """Lee el identificador usuario/nombre del dataset desde configs/datos.yaml."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["kaggle_dataset"]


def publish(data_dir, dataset_id, message, create=False):
    """Sube todos los Parquet de data_dir. create=True solo la primera vez.
    El dataset se crea privado: hay que agregar a los companeros como colaboradores en Kaggle.
    """
    data_dir = Path(data_dir)
    files = sorted(data_dir.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"no hay Parquet en {data_dir}")
    # Archivo de metadatos que exige la herramienta kaggle
    meta = {"title": "PTCG WP tablas procesadas", "id": dataset_id, "licenses": [{"name": "CC0-1.0"}]}
    (data_dir / "dataset-metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    if create:
        cmd = ["kaggle", "datasets", "create", "-p", str(data_dir)]
    else:
        cmd = ["kaggle", "datasets", "version", "-p", str(data_dir), "-m", message]
    # La herramienta kaggle puede fallar sin devolver un codigo de error:
    # por eso tambien se revisa si su mensaje contiene la palabra "error"
    res = subprocess.run(cmd, capture_output=True, text=True)
    salida = (res.stdout or "") + (res.stderr or "")
    print(salida)
    if res.returncode != 0 or "error" in salida.lower():
        raise RuntimeError("la publicacion fallo: revisa el mensaje de kaggle de arriba")
    print(f"publicados {len(files)} archivos en {dataset_id}")


def fetch(dataset_id, data_dir):
    """Descarga y descomprime los Parquet del dataset en data_dir.
    Muestra el mensaje de kaggle y falla con un error claro si no se pudo descargar.
    """
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        ["kaggle", "datasets", "download", "-d", dataset_id, "-p", str(data_dir), "--unzip"],
        capture_output=True, text=True,
    )
    salida = (res.stdout or "") + (res.stderr or "")
    print(salida)
    n = len(list(Path(data_dir).glob("*.parquet")))
    if res.returncode != 0 or n == 0:
        raise RuntimeError(
            f"no se pudo bajar {dataset_id}: revisa el mensaje de kaggle de arriba "
            "(401 = token incorrecto; 403 o 404 = tu usuario no tiene acceso al dataset)"
        )
    print(f"{n} Parquet en {data_dir}")


def main():
    """Linea de comandos: python -m ptcg_wp.store {publicar,bajar} ..."""
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["publicar", "bajar"])
    ap.add_argument("--config", default="configs/datos.yaml")
    ap.add_argument("--dir", default="/content/datos")
    ap.add_argument("-m", "--mensaje", default="actualizacion de tablas")
    ap.add_argument("--crear", action="store_true")
    args = ap.parse_args()
    dataset_id = load_dataset_id(args.config)
    if args.accion == "publicar":
        publish(args.dir, dataset_id, args.mensaje, args.crear)
    else:
        fetch(dataset_id, args.dir)


if __name__ == "__main__":
    main()