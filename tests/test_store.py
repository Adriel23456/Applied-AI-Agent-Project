"""Almacen en Kaggle: se prueba con una herramienta 'kaggle' falsa que imita al CLI real
(versiones que reemplazan todo, archivos sin subcarpetas, CSV entregados en .zip)."""
import os
import stat
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp import store  # noqa: E402

FAKE = textwrap.dedent('''\
    #!PYTHON
    import os, shutil, sys, zipfile
    from pathlib import Path
    ds = Path(os.environ["FAKE_KAGGLE_DIR"])
    a = sys.argv[1:]
    def opt(n):
        return a[a.index(n) + 1]
    with open(ds.parent / "llamadas.txt", "a") as f:
        f.write(" ".join(a[:2]) + "\\n")
    if a[:2] == ["datasets", "status"]:
        print("ready" if ds.exists() else "404 Client Error: Not Found"); sys.exit(0)
    if a[:2] == ["datasets", "download"]:
        nombre, dest = opt("-f"), Path(opt("-p"))
        src = ds / nombre
        if not src.exists():
            print("404 Client Error: Not Found for url"); sys.exit(0)
        if nombre.endswith(".csv"):
            with zipfile.ZipFile(dest / (nombre + ".zip"), "w") as z:
                z.write(src, nombre)
        else:
            shutil.copy(src, dest / nombre)
        print("Downloading", nombre); sys.exit(0)
    if a[:2] in (["datasets", "version"], ["datasets", "create"]):
        if a[1] == "create" and ds.exists():
            print("error: already exists"); sys.exit(0)
        if a[1] == "version" and not ds.exists():
            print("404 Client Error"); sys.exit(1)
        src = Path(opt("-p"))
        if any(p.is_dir() for p in src.iterdir()):
            print("error: subcarpetas"); sys.exit(1)
        shutil.rmtree(ds, ignore_errors=True); ds.mkdir()
        for p in src.iterdir():
            if p.name != "dataset-metadata.json":
                shutil.copy(p, ds / p.name)
        print("Dataset version is being created"); sys.exit(0)
    print("error: comando desconocido", a); sys.exit(2)
''').replace("PYTHON", sys.executable)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"; bin_dir.mkdir()
    exe = bin_dir / "kaggle"
    exe.write_text(FAKE)
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_KAGGLE_DIR", str(tmp_path / "dataset"))
    dias = tmp_path / "dias.yaml"; dias.write_text("dias: ['2026-01-01']\n")
    monkeypatch.setattr(store, "DIAS", dias)
    monkeypatch.setattr(store, "TRABAJO_DIR", tmp_path)
    monkeypatch.setattr(store, "INDICE_LOCAL", tmp_path / "indice_local.csv")
    datos = tmp_path / "datos"; datos.mkdir()
    for n in store.expected_files(["2026-01-01"]):
        (datos / n).write_bytes(n.encode())
    monkeypatch.setattr(store, "load_days", lambda _p: ["2026-01-01"])
    return tmp_path, datos


def _resultados(raiz, archivos):
    for ruta, contenido in archivos.items():
        (raiz / ruta).parent.mkdir(parents=True, exist_ok=True)
        (raiz / ruta).write_text(contenido)


def test_publicar_crea_aplana_y_listo_baja_y_verifica(entorno):
    tmp, datos = entorno
    raiz = tmp / "res"
    _resultados(raiz, {"b0_b1/metricas.csv": "a,b\n1,2\n", "b4/final/escenario_A/m.joblib": "bin"})
    store.publicar(store.archivos_de(raiz), "inicial", raiz=raiz, datos_dir=datos, dataset_id="u/d")
    nombres = sorted(p.name for p in (tmp / "dataset").iterdir())
    assert "results__b4__final__escenario_A__m.joblib" in nombres
    assert "results__indice.csv" in nombres and "particiones.parquet" in nombres
    # Otro servidor: sin copia local del indice ni archivos
    store.INDICE_LOCAL.unlink()
    otra = tmp / "otra"
    assert store.listo(["b0_b1/metricas.csv"], raiz=otra, dataset_id="u/d")
    assert (otra / "b0_b1/metricas.csv").read_text() == "a,b\n1,2\n"
    assert not store.listo(["b0_b1/metricas.csv", "b2/x.csv"], raiz=tmp / "vacia", dataset_id="u/d")
    assert not (tmp / "vacia").exists()  # todo o nada: no baja archivos sueltos


def test_publicar_conserva_resultados_previos_de_otros(entorno):
    tmp, datos = entorno
    _resultados(tmp / "a", {"b2/uno.csv": "1"})
    store.publicar(["b2/uno.csv"], "a", raiz=tmp / "a", datos_dir=datos, dataset_id="u/d")
    store.INDICE_LOCAL.unlink()  # companero en otro servidor
    _resultados(tmp / "b", {"b3/dos.csv": "2"})
    store.publicar(["b3/dos.csv"], "b", raiz=tmp / "b", datos_dir=datos, dataset_id="u/d")
    assert (tmp / "dataset" / "results__b2__uno.csv").exists()
    assert (tmp / "dataset" / "results__b3__dos.csv").exists()
    assert set(store.leer_indice("u/d")) >= {"b2/uno.csv", "b3/dos.csv", "particiones.parquet"}


def test_publicar_no_cambia_tablas_por_accidente(entorno):
    tmp, datos = entorno
    _resultados(tmp / "a", {"b2/uno.csv": "1"})
    store.publicar(["b2/uno.csv"], "a", raiz=tmp / "a", datos_dir=datos, dataset_id="u/d")
    (datos / "particiones.parquet").write_bytes(b"otra cosa")
    with pytest.raises(RuntimeError, match="distinta de la de Kaggle"):
        store.publicar(["b2/uno.csv"], "a", raiz=tmp / "a", datos_dir=datos, dataset_id="u/d")
    assert not store.tablas_al_dia(datos, "u/d")
    store.publicar([], "tablas", raiz=tmp / "a", actualizar_tablas=True, datos_dir=datos,
                   dataset_id="u/d")
    assert store.tablas_al_dia(datos, "u/d")


def test_asegurar_entrena_una_vez_y_luego_solo_baja(entorno, monkeypatch):
    tmp, datos = entorno
    monkeypatch.setattr(store, "DATOS_DIR", datos)
    monkeypatch.setattr(store, "load_dataset_id", lambda *a: "u/d")
    raiz = tmp / "res"
    llamadas = []

    def entrenar():
        llamadas.append(1)
        _resultados(raiz, {"b4/final/escenario_A/m.csv": "x"})

    rutas = ["b4/final/escenario_A/m.csv"]
    _resultados(tmp / "x", {"b0/a.csv": "0"})
    store.publicar(["b0/a.csv"], "base", raiz=tmp / "x", datos_dir=datos, dataset_id="u/d")
    assert store.asegurar(rutas, entrenar, "m", raiz=raiz) == "publicado"
    assert store.asegurar(rutas, entrenar, "m", raiz=tmp / "nuevo") == "kaggle"
    assert llamadas == [1]
    with pytest.raises(RuntimeError, match="no produjo"):
        store.asegurar(["b9/nada.csv"], lambda: None, "m", raiz=raiz)


def test_rutas_no_validas():
    with pytest.raises(ValueError):
        store.nombre_kaggle("b4/../x.csv")
    with pytest.raises(ValueError):
        store.nombre_kaggle("b4/a__b.csv")
    assert store.nombre_kaggle("b4/final/x.joblib") == "results__b4__final__x.joblib"

def test_sin_indice_no_se_asume_vacio(entorno, monkeypatch):
    tmp, datos = entorno
    (tmp / "dataset").mkdir()  # dataset existe pero sin indice (version procesandose)
    monkeypatch.setattr(store.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="no se pudo bajar"):
        store.listo(["b2/uno.csv"], raiz=tmp / "r", dataset_id="u/d")
    assert store.leer_indice("u/d", requerido=False) == {}