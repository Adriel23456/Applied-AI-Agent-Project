"""Almacen del equipo en un dataset PRIVADO de Kaggle: tablas procesadas y resultados.

Un solo dataset (configs/datos.yaml) guarda dos cosas:
  - Tablas: estados_*.parquet, partidas_*.parquet y particiones.parquet (receta en ingest.py).
  - Resultados: CSV, JSON, SQLite y .joblib de los modelos. Kaggle no guarda subcarpetas, asi
    que la ruta se aplana: b4/final/escenario_A/x.joblib -> results__b4__final__escenario_A__x.joblib
El archivo results__indice.csv lista TODO lo que hay en el dataset (ruta, bytes, sha256,
fecha y commit). Con el se decide, archivo por archivo, si algo ya existe en Kaggle.

Reglas importantes de Kaggle que este modulo resuelve:
  - Cada version nueva REEMPLAZA todos los archivos del dataset. Por eso publicar() siempre
    sube la union: tablas + todos los resultados ya indexados + los nuevos.
  - La descarga del dataset completo puede responder 404; se baja archivo por archivo.
  - La herramienta kaggle puede fallar devolviendo codigo 0: se revisa el texto de salida.
  - Una version recien subida tarda unos minutos en verse. Por eso se guarda una copia local
    del ultimo indice publicado y se combina con el de Kaggle.

Uso desde los cuadernos:
  store.listo(rutas)                         -> True si TODAS estan en Kaggle (y las baja)
  store.asegurar(rutas, entrenar, mensaje)   -> baja si existen; si no, entrena y publica
  store.publicar(rutas, mensaje)             -> sube resultados nuevos sin perder nada
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ptcg_wp.ingest import load_days

REPO_DIR = Path(__file__).resolve().parents[2]
CONFIG = REPO_DIR / "configs" / "datos.yaml"
DIAS = REPO_DIR / "configs" / "dias.yaml"
DATOS_DIR = Path("/content/datos")
RESULTADOS_DIR = Path("/content/resultados")
TRABAJO_DIR = Path("/content") if Path("/content").exists() else Path(tempfile.gettempdir())
INDICE_LOCAL = TRABAJO_DIR / ".ptcg_indice_publicado.csv"

PREFIJO = "results__"
INDICE = "results__indice.csv"
META = "__publicacion__"  # fila del indice con la fecha de la version (no es un archivo)
CAMPOS = ["ruta", "archivo_kaggle", "tipo", "bytes", "sha256", "fecha_utc", "commit"]


# ----------------------------------------------------------------------------------------
# Utilidades basicas
# ----------------------------------------------------------------------------------------

def load_dataset_id(config_path=CONFIG):
    """Lee el identificador usuario/nombre del dataset desde configs/datos.yaml."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["kaggle_dataset"]


def expected_files(days):
    """Nombres de las tablas que debe tener el dataset para la lista de dias dada."""
    return ([f"estados_{d}.parquet" for d in days]
            + [f"partidas_{d}.parquet" for d in days]
            + ["particiones.parquet"])


def nombre_kaggle(ruta):
    """Ruta relativa de resultados -> nombre plano del archivo dentro del dataset."""
    ruta = Path(ruta).as_posix()
    partes = ruta.split("/")
    if ruta.startswith("/") or any(p in ("", ".", "..") or "__" in p for p in partes):
        raise ValueError(f"ruta de resultado no valida (sin '__', sin '..', relativa): {ruta}")
    return PREFIJO + "__".join(partes)


def sha256(path):
    """Huella SHA-256 de un archivo, leyendo por bloques (sirve para archivos de GB)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _commit():
    """Commit corto del repo, para dejar trazabilidad en el indice."""
    try:
        return subprocess.check_output(["git", "-C", str(REPO_DIR), "rev-parse", "--short", "HEAD"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "desconocido"


def _kaggle(args):
    """Ejecuta la herramienta kaggle. Devuelve (ok, texto). ok exige codigo 0 y ningun error
    en el texto, porque kaggle a veces falla devolviendo 0."""
    res = subprocess.run(["kaggle", *args], capture_output=True, text=True)
    texto = (res.stdout or "") + (res.stderr or "")
    bajo = texto.lower()
    malo = res.returncode != 0 or any(p in bajo for p in ("error", "not found", "forbidden",
                                                            "unauthorized"))
    return not malo, texto


def _error_de_acceso(texto):
    """401 o 403: el problema es el token o el permiso, no que falte un archivo."""
    if not re.search(r"(?i)error|forbidden|unauthorized", texto):
        return None
    if re.search(r"\b401\b", texto):
        return "401: el token de Kaggle es incorrecto (vuelve a ejecutar la celda de preparacion)"
    if re.search(r"\b403\b", texto):
        return "403: tu usuario de Kaggle no tiene acceso al dataset (pide que te agreguen)"
    return None


def _bajar_archivo(dataset_id, nombre, destino):
    """Baja UN archivo del dataset y lo deja en 'destino'. Devuelve (ok, texto de kaggle).
    Kaggle puede entregar el archivo comprimido en .zip: se descomprime aqui."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kaggle-bajada-", dir=TRABAJO_DIR) as tmp:
        tmp = Path(tmp)
        _, texto = _kaggle(["datasets", "download", "-d", dataset_id, "-f", nombre, "-p", str(tmp)])
        for z in tmp.glob("*.zip"):
            if z.name == nombre:
                continue  # el archivo pedido era un zip de verdad
            with zipfile.ZipFile(z) as zf:
                zf.extractall(tmp)
            z.unlink()
        bajado = tmp / nombre
        if not bajado.exists():
            acceso = _error_de_acceso(texto)
            if acceso:
                raise RuntimeError(f"Kaggle respondio {acceso}\n{texto}")
            return False, texto
        shutil.move(str(bajado), str(destino))
    return True, texto


# ----------------------------------------------------------------------------------------
# Tablas
# ----------------------------------------------------------------------------------------

def fetch(dataset_id, data_dir, names, estricto=True):
    """Baja, UNO POR UNO, las tablas indicadas en 'names' que no existan en data_dir.
    estricto=True lanza error si alguna falta; estricto=False devuelve la lista de faltantes
    (lo usa 00_arranque para decidir si hay que procesar dias desde los JSON crudos)."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    fallidos = []
    for name in names:
        if (data_dir / name).exists():
            print(f"ya existe: {name}")
            continue
        ok, texto = _bajar_archivo(dataset_id, name, data_dir / name)
        if ok:
            print(f"bajado: {name}")
        else:
            fallidos.append(name)
            print(f"no esta en Kaggle: {name}\n{texto.strip()}")
    if fallidos and estricto:
        raise RuntimeError(f"no se pudieron bajar {len(fallidos)} tablas de {dataset_id}: "
                           "revisa los mensajes de arriba")
    print(f"{len(list(data_dir.glob('*.parquet')))} Parquet en {data_dir}")
    return fallidos


def dataset_existe(dataset_id):
    """True si el dataset existe y este usuario lo puede ver."""
    ok, texto = _kaggle(["datasets", "status", dataset_id])
    if ok:
        return True
    acceso = _error_de_acceso(texto)
    if acceso and "401" in acceso:
        raise RuntimeError(f"Kaggle respondio {acceso}\n{texto}")
    return False


# ----------------------------------------------------------------------------------------
# Indice
# ----------------------------------------------------------------------------------------

def _leer_csv_indice(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {fila["ruta"]: fila for fila in csv.DictReader(f)}


def _escribir_csv_indice(filas, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for ruta in sorted(filas):
            w.writerow({c: filas[ruta].get(c, "") for c in CAMPOS})


def leer_indice(dataset_id=None, requerido=True, intentos=10, espera_s=60):
    """Indice del dataset: {ruta: fila}. Combina el de Kaggle con el ultimo publicado desde este
    servidor (Kaggle tarda unos minutos en mostrar una version nueva).

    Si el indice no se puede bajar, NO se asume que el dataset esta vacio: justo despues de una
    publicacion Kaggle responde "no encontrado" mientras procesa la version nueva, y asumir vacio
    haria que una celda reentrene horas por nada. Se reintenta 'intentos' veces cada 'espera_s'
    segundos y, si sigue sin aparecer, se lanza un error. requerido=False (solo publicar) acepta
    un dataset sin indice, que es el caso de la primera subida de resultados.
    """
    dataset_id = dataset_id or load_dataset_id()
    remoto, texto = None, ""
    for intento in range(1, intentos + 1):
        with tempfile.TemporaryDirectory(prefix="kaggle-indice-", dir=TRABAJO_DIR) as tmp:
            ok, texto = _bajar_archivo(dataset_id, INDICE, Path(tmp) / INDICE)
            if ok:
                remoto = _leer_csv_indice(Path(tmp) / INDICE)
        if remoto is not None or not requerido:
            break
        if intento < intentos:
            print(f"{INDICE} todavia no responde (Kaggle puede estar procesando una version "
                  f"nueva); reintento {intento}/{intentos - 1} en {espera_s} s")
            time.sleep(espera_s)
    if remoto is None:
        if requerido:
            raise RuntimeError(f"no se pudo bajar {INDICE} de {dataset_id} tras {intentos} intentos. "
                               "Si alguien acaba de publicar, espera unos minutos y vuelve a ejecutar "
                               f"la celda. Mensaje de kaggle:\n{texto.strip()}")
        print(f"aviso: {INDICE} no esta en Kaggle (dataset sin resultados publicados todavia)")
        remoto = {}
    # La copia local (ultima publicacion hecha desde este servidor) reemplaza a la de Kaggle
    # solo si es MAS NUEVA: Kaggle tarda en servir una version recien subida, y una version
    # posterior de un companero debe ganar sobre la copia local.
    if INDICE_LOCAL.exists():
        local = _leer_csv_indice(INDICE_LOCAL)
        fecha_local = local.get(META, {}).get("fecha_utc", "")
        fecha_remota = remoto.get(META, {}).get("fecha_utc", "")
        if (local.get("__dataset__", {}).get("archivo_kaggle") == dataset_id
                and fecha_local > fecha_remota):
            remoto = local
    return {r: f for r, f in remoto.items() if f.get("tipo") in ("tabla", "resultado")}


def faltantes(rutas, dataset_id=None, indice=None):
    """Rutas de resultados que NO estan en Kaggle."""
    indice = leer_indice(dataset_id) if indice is None else indice
    return [r for r in rutas if r not in indice]


# ----------------------------------------------------------------------------------------
# Resultados: bajar, publicar, asegurar
# ----------------------------------------------------------------------------------------

def _traer(dataset_id, fila, raiz):
    """Deja en raiz/ruta el archivo de la fila del indice, verificando su sha256.
    Si ya esta local con el mismo sha256, no lo baja."""
    destino = Path(raiz) / fila["ruta"]
    if destino.exists() and sha256(destino) == fila["sha256"]:
        return "ya local"
    ok, texto = _bajar_archivo(dataset_id, fila["archivo_kaggle"], destino)
    if not ok:
        raise RuntimeError(f"el indice dice que {fila['archivo_kaggle']} existe, pero no se pudo "
                           f"bajar (si se publico hace poco, espera unos minutos):\n{texto}")
    if sha256(destino) != fila["sha256"]:
        raise RuntimeError(f"{fila['ruta']}: el sha256 bajado no coincide con el indice")
    return "bajado"


def listo(rutas, raiz=None, dataset_id=None):
    """True si TODAS las rutas estan en Kaggle; en ese caso las deja en raiz (bajando solo las
    que falten localmente). Si falta alguna, no baja nada y devuelve False."""
    dataset_id = dataset_id or load_dataset_id()
    raiz = Path(raiz or RESULTADOS_DIR)
    indice = leer_indice(dataset_id)
    faltan = faltantes(rutas, indice=indice)
    if faltan:
        print(f"No estan en Kaggle ({len(faltan)} de {len(rutas)}):")
        for r in faltan:
            print("   -", r)
        return False
    for r in rutas:
        print(f"{_traer(dataset_id, indice[r], raiz)}: {r}")
    return True


def _enlazar(origen, destino):
    """Pone 'origen' en la carpeta de subida sin copiar bytes (enlace duro) si se puede."""
    try:
        os.link(origen, destino)
    except OSError:
        shutil.copy2(origen, destino)


def publicar(rutas, mensaje, raiz=None, actualizar_tablas=False,
             datos_dir=None, dataset_id=None, excluir=()):
    """Sube una version nueva del dataset con: tablas + todos los resultados ya indexados +
    las 'rutas' nuevas (que deben existir en raiz). Crea el dataset si no existe.

    actualizar_tablas=False exige que las tablas locales sean IDENTICAS a las del indice (asi
    publicar un resultado nunca cambia las tablas por accidente). Solo 00_arranque usa True,
    cuando reconstruyo tablas a proposito.
    excluir: rutas de resultados que NO pasan a la version nueva (las usa eliminar()).
    """
    dataset_id = dataset_id or load_dataset_id()
    raiz, datos_dir = Path(raiz or RESULTADOS_DIR), Path(datos_dir or DATOS_DIR)
    existe = dataset_existe(dataset_id)
    indice = leer_indice(dataset_id, requerido=False) if existe else {}
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    commit = _commit()
    nuevo = {}

    # 1) Tablas: siempre deben estar en esta carpeta local
    tablas = expected_files(load_days(DIAS))
    sin_tabla = [t for t in tablas if not (datos_dir / t).exists()]
    if sin_tabla:
        raise RuntimeError(f"faltan tablas locales en {datos_dir}: {sin_tabla}. "
                           "Ejecuta la celda de preparacion (las baja de Kaggle).")
    tablas_en_indice = {r: f for r, f in indice.items() if f.get("tipo") == "tabla"}
    for t in tablas:
        huella = sha256(datos_dir / t)
        previa = tablas_en_indice.get(t)
        if previa and previa["sha256"] != huella and not actualizar_tablas:
            raise RuntimeError(f"la tabla local {t} es distinta de la de Kaggle; no se publica para "
                               "no reemplazar las tablas del equipo. Borra /content/datos y vuelve "
                               "a ejecutar la preparacion.")
        if previa and previa["sha256"] == huella:
            nuevo[t] = previa
        else:
            nuevo[t] = {"ruta": t, "archivo_kaggle": t, "tipo": "tabla",
                        "bytes": (datos_dir / t).stat().st_size, "sha256": huella,
                        "fecha_utc": fecha, "commit": commit}

    # 2) Resultados que ya estaban: se traen si no estan locales (Kaggle reemplaza todo)
    rutas = [Path(r).as_posix() for r in rutas]
    excluir = {Path(r).as_posix() for r in excluir}
    for r, fila in indice.items():
        if fila.get("tipo") == "resultado" and r not in rutas and r not in excluir:
            _traer(dataset_id, fila, raiz)
            nuevo[r] = fila

    # 3) Resultados nuevos o cambiados
    for r in rutas:
        local = raiz / r
        if not local.is_file():
            raise FileNotFoundError(f"no existe el resultado a publicar: {local}")
        huella = sha256(local)
        previa = indice.get(r)
        if previa and previa["sha256"] == huella:
            nuevo[r] = previa
        else:
            nuevo[r] = {"ruta": r, "archivo_kaggle": nombre_kaggle(r), "tipo": "resultado",
                        "bytes": local.stat().st_size, "sha256": huella,
                        "fecha_utc": fecha, "commit": commit}
            print(("reemplaza: " if previa else "nuevo: ") + r)

    # 4) Carpeta plana de subida + indice + metadatos, y subida
    with tempfile.TemporaryDirectory(prefix="kaggle-subida-", dir=TRABAJO_DIR) as tmp:
        tmp = Path(tmp)
        for r, fila in nuevo.items():
            origen = datos_dir / r if fila["tipo"] == "tabla" else raiz / r
            _enlazar(origen, tmp / fila["archivo_kaggle"])
        nuevo_con_fecha = dict(nuevo)
        nuevo_con_fecha[META] = {"ruta": META, "tipo": "meta", "fecha_utc": fecha, "commit": commit}
        _escribir_csv_indice(nuevo_con_fecha, tmp / INDICE)
        meta = {"title": "PTCG WP tablas procesadas", "id": dataset_id,
                "licenses": [{"name": "CC0-1.0"}]}
        (tmp / "dataset-metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        if existe:
            cmd = ["datasets", "version", "-p", str(tmp), "-m", f"{mensaje} (commit {commit})"]
        else:
            print(f"el dataset {dataset_id} no existe: se crea (privado)")
            cmd = ["datasets", "create", "-p", str(tmp)]
        ok, texto = _kaggle(cmd)
        print(texto.strip())
        if not ok:
            raise RuntimeError("la publicacion fallo: revisa el mensaje de kaggle de arriba. "
                               "Los archivos siguen en este servidor; vuelve a ejecutar la celda.")

    # 5) Copia local del indice publicado (Kaggle tarda en mostrar la version nueva)
    copia = dict(nuevo_con_fecha)
    copia["__dataset__"] = {"ruta": "__dataset__", "archivo_kaggle": dataset_id}
    _escribir_csv_indice(copia, INDICE_LOCAL)
    n_res = sum(1 for f in nuevo.values() if f["tipo"] == "resultado")
    print(f"publicado en {dataset_id}: {len(tablas)} tablas + {n_res} resultados "
          f"({len(rutas)} de esta celda)")


def asegurar(rutas, entrenar, mensaje, raiz=None):
    """Patron de cada celda que entrena:
      1) Si TODAS las rutas estan en Kaggle: las baja y termina (no entrena).
      2) Si no: entrena (salvo que ya esten completas en este servidor por una corrida anterior
         que no alcanzo a publicarse), verifica que existan y publica.
    Devuelve 'kaggle' o 'publicado'."""
    raiz = Path(raiz or RESULTADOS_DIR)
    if listo(rutas, raiz):
        print("=> Todo estaba en Kaggle: se bajo y NO se entreno.")
        return "kaggle"
    if all((Path(raiz) / r).is_file() for r in rutas):
        print("=> Los archivos ya estaban completos en este servidor: solo se publican.")
    else:
        print("=> Se entrena.")
        entrenar()
    sin_crear = [r for r in rutas if not (Path(raiz) / r).is_file()]
    if sin_crear:
        raise RuntimeError(f"el entrenamiento no produjo estos archivos: {sin_crear}")
    publicar(rutas, mensaje, raiz)
    return "publicado"


def eliminar(prefijo, mensaje, raiz=None, datos_dir=None, dataset_id=None):
    """Quita de Kaggle y de este servidor todos los resultados cuya ruta empieza con 'prefijo'
    (por ejemplo "b4/h2/"). Publica una version nueva sin ellos; las tablas y el resto de los
    resultados se conservan. Si en Kaggle no hay nada con ese prefijo, solo limpia lo local.
    Devuelve la lista de rutas quitadas de Kaggle."""
    if not prefijo or prefijo.strip("/") == "" or ".." in prefijo:
        raise ValueError("indica un prefijo concreto, por ejemplo 'b4/h2/'")
    dataset_id = dataset_id or load_dataset_id()
    raiz = Path(raiz or RESULTADOS_DIR)
    indice = leer_indice(dataset_id)
    quitar = sorted(r for r, f in indice.items() if f["tipo"] == "resultado" and r.startswith(prefijo))
    locales = [p for p in sorted((raiz / prefijo).parent.rglob("*"))
               if p.is_file() and p.relative_to(raiz).as_posix().startswith(prefijo)]
    for p in locales:
        p.unlink()
        print("borrado local:", p.relative_to(raiz).as_posix())
    if not quitar:
        print(f"En Kaggle no hay resultados que empiecen con '{prefijo}': no se publica nada.")
        return []
    for r in quitar:
        print("se quita de Kaggle:", r)
    publicar([], mensaje, raiz=raiz, datos_dir=datos_dir, dataset_id=dataset_id, excluir=quitar)
    return quitar


def archivos_de(carpeta):
    """Rutas relativas (con /) de todos los archivos bajo una carpeta, en orden."""
    carpeta = Path(carpeta)
    return [p.relative_to(carpeta).as_posix() for p in sorted(carpeta.rglob("*")) if p.is_file()]


def tablas_al_dia(datos_dir=None, dataset_id=None):
    """True si las tablas locales son exactamente las publicadas en Kaggle."""
    indice = leer_indice(dataset_id)
    for t in expected_files(load_days(DIAS)):
        fila, local = indice.get(t), Path(datos_dir or DATOS_DIR) / t
        if fila is None or not local.exists() or sha256(local) != fila["sha256"]:
            return False
    return True


def main():
    """Linea de comandos:
      python -m ptcg_wp.store bajar     [--dir /content/datos]
      python -m ptcg_wp.store publicar  [--dir /content/datos] -m "mensaje"   (tablas nuevas)
      python -m ptcg_wp.store subir-resultados --desde results -m "mensaje"
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["publicar", "bajar", "subir-resultados"])
    ap.add_argument("--config", default=str(CONFIG))
    ap.add_argument("--dir", default=str(DATOS_DIR))
    ap.add_argument("--desde", default=str(REPO_DIR / "results"))
    ap.add_argument("-m", "--mensaje", default="actualizacion")
    args = ap.parse_args()
    dataset_id = load_dataset_id(args.config)
    if args.accion == "bajar":
        fetch(dataset_id, args.dir, expected_files(load_days(DIAS)))
    elif args.accion == "publicar":
        publicar([], args.mensaje, actualizar_tablas=True, datos_dir=args.dir, dataset_id=dataset_id)
    else:
        rutas = archivos_de(args.desde)
        print(f"{len(rutas)} archivos de resultados en {args.desde}")
        publicar(rutas, args.mensaje, raiz=args.desde, datos_dir=args.dir, dataset_id=dataset_id)


if __name__ == "__main__":
    main()