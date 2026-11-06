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


def _configure_kaggle(credential):
    """Valida una credencial y configura el entorno sin imprimir su contenido."""
    if isinstance(credential, str):
        value = credential.strip()
        if value.startswith("{"):
            try:
                credential = json.loads(value)
            except json.JSONDecodeError as exc:
                raise TypeError("El JSON de credenciales Kaggle no es válido.") from exc
        else:
            credential = value

    if isinstance(credential, dict):
        normalized = {str(key).lower(): value for key, value in credential.items()}
        token = next((normalized[key] for key in
                      ("kaggle_api_token", "api_token", "access_token", "token")
                      if normalized.get(key)), None)
        if isinstance(token, str) and token.strip():
            os.environ.pop("KAGGLE_USERNAME", None)
            os.environ.pop("KAGGLE_KEY", None)
            os.environ["KAGGLE_API_TOKEN"] = token.strip()
            return

        username = normalized.get("username")
        key = normalized.get("key")
        if isinstance(username, str) and username.strip() and isinstance(key, str) and key.strip():
            os.environ.pop("KAGGLE_API_TOKEN", None)
            os.environ["KAGGLE_USERNAME"] = username.strip()
            os.environ["KAGGLE_KEY"] = key.strip()
            return

        raise TypeError(
            "El secreto KAGGLE_API_TOKEN es un objeto, pero no contiene un token "
            "reconocible ni los campos legacy 'username' y 'key'."
        )

    if isinstance(credential, str) and credential:
        os.environ.pop("KAGGLE_USERNAME", None)
        os.environ.pop("KAGGLE_KEY", None)
        os.environ["KAGGLE_API_TOKEN"] = credential
        return

    raise TypeError("KAGGLE_API_TOKEN debe ser un token de texto o credenciales Kaggle válidas.")


def setup_kaggle(prompt_on_invalid=True):
    """Configura Kaggle; si el secreto no es válido, ofrece entrada oculta una vez.

    Acepta un token de texto o un JSON de credenciales legacy. Para uso sin
    interacción, ``prompt_on_invalid=False`` conserva el error original.
    Nunca imprime el secreto ni los valores ingresados.
    """
    # Si este kernel ya tiene credenciales (celda ejecutada antes), no se vuelve a pedir nada
    if os.environ.get("KAGGLE_API_TOKEN") or (os.environ.get("KAGGLE_USERNAME")
                                              and os.environ.get("KAGGLE_KEY")):
        print("Kaggle ya estaba configurado en este kernel")
        return
    credential = read_secret("KAGGLE_API_TOKEN")
    try:
        _configure_kaggle(credential)
    except TypeError:
        if not prompt_on_invalid:
            raise
        print("El secreto KAGGLE_API_TOKEN de Colab no tiene un formato reconocido. "
              "Ingresa un token Kaggle válido o el JSON legacy en el campo oculto.")
        replacement = getpass("Token Kaggle o JSON legacy (entrada oculta): ")
        try:
            _configure_kaggle(replacement)
        except TypeError as exc:
            raise TypeError("La credencial ingresada no tiene un formato válido para Kaggle.") from exc


def recursos():
    """Imprime y devuelve los nucleos de CPU y la RAM del servidor (total y disponible).
    Sirve para confirmar que Colab entrego el tipo de servidor esperado (CPU + RAM alta:
    8 nucleos y unos 51 GiB) antes de entrenar."""
    nucleos = os.cpu_count()
    try:
        nucleos_usables = len(os.sched_getaffinity(0))
    except AttributeError:
        nucleos_usables = nucleos
    memoria = {}
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for linea in f:
                nombre, valor = linea.split(":", 1)
                memoria[nombre] = int(valor.split()[0]) / 1024 ** 2  # kB -> GiB
    except OSError:
        pass
    total, libre = memoria.get("MemTotal"), memoria.get("MemAvailable")
    texto_ram = (f"RAM total {total:.1f} GiB | disponible {libre:.1f} GiB"
                 if total is not None else "RAM: no disponible en este sistema")
    print(f"Nucleos de CPU: {nucleos} (usables por este proceso: {nucleos_usables}) | {texto_ram}")
    return {"nucleos": nucleos, "nucleos_usables": nucleos_usables,
            "ram_total_gib": total, "ram_disponible_gib": libre}
