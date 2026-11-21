"""Registro de invocaciones en JSONL: una linea por llamada a una herramienta o a un agente.

Es la evidencia de que el agente consume el modelo: cada linea dice quien llamo, a que
herramienta, con que entrada (resumida), que devolvio, cuanto tardo, con que modelo
(SHA-256) y con que version del codigo (commit).

Ubicacion: <repo>/registros/agente_AAAA-MM-DD.jsonl (fuera de Git). Las sesiones que sirven
como evidencia se copian a docx/03Evidencia/.
"""

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ptcg_agente.artefactos import REPO_DIR

REGISTROS_DIR = Path(os.environ.get("PTCG_REGISTROS", REPO_DIR / "registros"))
MAX_TEXTO = 400


def resumir(valor):
    """Resumen corto y estable de una entrada: las observaciones se reducen a su hash."""
    if isinstance(valor, dict):
        texto = json.dumps(valor, sort_keys=True, default=str)
        if len(texto) > MAX_TEXTO:
            return {"sha256": hashlib.sha256(texto.encode()).hexdigest()[:16], "bytes": len(texto)}
        return valor
    if isinstance(valor, list):
        return [resumir(v) for v in valor]
    if isinstance(valor, str) and len(valor) > MAX_TEXTO:
        return valor[:MAX_TEXTO] + "..."
    return valor


class Registro:
    def __init__(self, agente, modelo_sha256=None, commit=None, carpeta=None, sesion=None):
        self.agente = agente
        self.modelo_sha256 = modelo_sha256
        self.commit = commit
        self.sesion = sesion or uuid.uuid4().hex[:12]
        self.carpeta = Path(carpeta or REGISTROS_DIR)

    @property
    def archivo(self):
        dia = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.carpeta / f"agente_{dia}.jsonl"

    def anotar(self, herramienta, entrada, salida, duracion_ms, agente=None):
        linea = {
            "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "sesion": self.sesion,
            "agente": agente or self.agente,
            "herramienta": herramienta,
            "entrada": {k: resumir(v) for k, v in (entrada or {}).items()},
            "salida": salida,
            "duracion_ms": round(duracion_ms, 1),
            "modelo_sha256": self.modelo_sha256,
            "commit": self.commit,
        }
        self.carpeta.mkdir(parents=True, exist_ok=True)
        with open(self.archivo, "a", encoding="utf-8") as f:
            f.write(json.dumps(linea, ensure_ascii=False, default=str) + "\n")
        return linea

    def medir(self, herramienta, entrada, funcion, agente=None):
        """Ejecuta funcion(), anota la llamada y devuelve su salida."""
        inicio = time.perf_counter()
        salida = funcion()
        self.anotar(herramienta, entrada, salida, 1000 * (time.perf_counter() - inicio), agente)
        return salida