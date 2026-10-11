"""Almacen de las tablas procesadas en un dataset PRIVADO de Kaggle.

El repo guarda la receta (ingest.py + dias.yaml); este dataset guarda el resultado
para no repetir ~12 minutos de ingesta por dia en cada servidor nuevo de Colab.
  publicar : sube los Parquet de una carpeta como nueva version del dataset
  bajar    : descarga los Parquet del dataset a una carpeta, archivo por archivo
"""

import argparse
import json
import subprocess
import zipfile
from pathlib import Path

import yaml

from ptcg_wp.ingest import load_days


def load_dataset_id(config_path):
    """Lee el identificador usuario/nombre del dataset desde configs/datos.yaml."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["kaggle_dataset"]


def expected_files(days):
    """Nombres de los archivos que debe tener el dataset para la lista de dias dada."""
    return ([f"estados_{d}.parquet" for d in days]
            + [f"partidas_{d}.parquet" for d in days]
            + ["particiones.parquet"])


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


def fetch(dataset_id, data_dir, names):
    """Descarga del dataset, UNO POR UNO, los archivos indicados en 'names'.
    Se baja archivo por archivo porque la descarga del dataset completo (un solo zip)
    puede responder 404 aunque se tenga acceso. Los archivos que ya existen se omiten.
    Si kaggle entrega un archivo comprimido (.zip), se descomprime y se borra el zip.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    failed = []
    for name in names:
        if (data_dir / name).exists():
            print(f"ya existe: {name}")
            continue
        res = subprocess.run(
            ["kaggle", "datasets", "download", "-d", dataset_id, "-f", name, "-p", str(data_dir)],
            capture_output=True, text=True,
        )
        for z in data_dir.glob("*.zip"):
            with zipfile.ZipFile(z) as zf:
                zf.extractall(data_dir)
            z.unlink()
        if (data_dir / name).exists():
            print(f"bajado: {name}")
        else:
            failed.append(name)
            print(f"FALLO: {name}\n{(res.stdout or '') + (res.stderr or '')}")
    if failed:
        raise RuntimeError(
            f"no se pudieron bajar {len(failed)} archivos de {dataset_id}: revisa los mensajes de arriba "
            "(401 = token incorrecto; 403 = tu usuario no tiene acceso al dataset)"
        )
    print(f"{len(list(data_dir.glob('*.parquet')))} Parquet en {data_dir}")


def main():
    """Linea de comandos: python -m ptcg_wp.store {publicar,bajar} ..."""
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["publicar", "bajar"])
    ap.add_argument("--config", default="configs/datos.yaml")
    ap.add_argument("--dias", default="configs/dias.yaml")
    ap.add_argument("--dir", default="/content/datos")
    ap.add_argument("-m", "--mensaje", default="actualizacion de tablas")
    ap.add_argument("--crear", action="store_true")
    args = ap.parse_args()
    dataset_id = load_dataset_id(args.config)
    if args.accion == "publicar":
        publish(args.dir, dataset_id, args.mensaje, args.crear)
    else:
        fetch(dataset_id, args.dir, expected_files(load_days(args.dias)))


if __name__ == "__main__":
    main()