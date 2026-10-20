"""Utilidades para trabajar en Colab: lectura de secretos y configuracion de Kaggle."""

import json
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
    """Configure Kaggle auth from a token string or legacy credential object.

    Colab secrets may contain either the current API token string or a parsed
    JSON object copied from Kaggle's legacy ``kaggle.json`` download.
    """
    credential = read_secret("KAGGLE_API_TOKEN")
    if isinstance(credential, str):
        value = credential.strip()
        if value.startswith("{"):
            try:
                credential = json.loads(value)
            except json.JSONDecodeError:
                credential = value
        else:
            credential = value

    if isinstance(credential, dict):
        normalized = {str(key).lower(): value for key, value in credential.items()}
        token = next((normalized[key] for key in
                      ("kaggle_api_token", "api_token", "access_token", "token")
                      if normalized.get(key)), None)
        if isinstance(token, str) and token.strip():
            os.environ["KAGGLE_API_TOKEN"] = token.strip()
            return

        username = normalized.get("username")
        key = normalized.get("key")
        if isinstance(username, str) and username.strip() and isinstance(key, str) and key.strip():
            # Kaggle's legacy JSON credentials use username/key, not an API token.
            os.environ.pop("KAGGLE_API_TOKEN", None)
            os.environ["KAGGLE_USERNAME"] = username.strip()
            os.environ["KAGGLE_KEY"] = key.strip()
            return

        raise TypeError(
            "El secreto KAGGLE_API_TOKEN es un objeto, pero no contiene un token "
            "reconocible ni los campos legacy 'username' y 'key'. Guarda un token "
            "de Kaggle como texto o un kaggle.json con esos dos campos."
        )

    if isinstance(credential, str) and credential:
        os.environ["KAGGLE_API_TOKEN"] = credential
        return

    raise TypeError(
        "KAGGLE_API_TOKEN debe ser un token de texto o un objeto de credenciales Kaggle."
    )
