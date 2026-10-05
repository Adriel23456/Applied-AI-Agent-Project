"""Utilidades para trabajar en Colab: lectura de secretos y configuracion de Kaggle."""

import os
from getpass import getpass

# Ruta donde se busca el archivo de secretos si no se esta en la interfaz web de Colab
SECRETS_PATH = "/content/secrets.txt"


def read_secret(name, path=SECRETS_PATH):
    """Devuelve el valor de un secreto. Prueba tres fuentes, en este orden:
    1) Secretos de Colab (solo funciona en la pagina web de Colab, no desde VS Code)
    2) Archivo secrets.txt: una linea con el nombre y la siguiente con el valor
    3) Pedirlo a mano con getpass (no se muestra mientras se escribe)
    """
    # Fuente 1: en VS Code lanza TimeoutException, por eso se captura y se sigue
    try:
        from google.colab import userdata
        return userdata.get(name)
    except Exception:
        pass

    # Fuente 2: leer secrets.txt ignorando lineas vacias
    # utf-8-sig elimina el caracter invisible que Windows agrega al inicio del archivo
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        for i, line in enumerate(lines):
            # El valor esta en la linea siguiente a la que contiene el nombre
            if line == name and i + 1 < len(lines):
                return lines[i + 1]

    # Fuente 3: ultimo recurso, pedirlo al usuario
    return getpass(f"{name}: ")


def setup_kaggle():
    """Deja el token de Kaggle en la variable de entorno que usa la herramienta kaggle."""
    os.environ["KAGGLE_API_TOKEN"] = read_secret("KAGGLE_API_TOKEN")