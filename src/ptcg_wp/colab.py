import os
from getpass import getpass

SECRETS_PATH = "/content/secrets.txt"


def read_secret(name, path=SECRETS_PATH):
    try:
        from google.colab import userdata
        return userdata.get(name)
    except Exception:
        pass
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        for i, line in enumerate(lines):
            if line == name and i + 1 < len(lines):
                return lines[i + 1]
    return getpass(f"{name}: ")


def setup_kaggle():
    os.environ["KAGGLE_API_TOKEN"] = read_secret("KAGGLE_API_TOKEN")