"""Kaggle auth accepts current tokens and legacy JSON credentials safely."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp import colab


def test_setup_kaggle_accepts_plain_api_token(monkeypatch):
    monkeypatch.setattr(colab, "read_secret", lambda _name: " token-value ")
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)

    colab.setup_kaggle()

    assert colab.os.environ["KAGGLE_API_TOKEN"] == "token-value"


def test_setup_kaggle_accepts_token_inside_json_secret(monkeypatch):
    monkeypatch.setattr(colab, "read_secret", lambda _name: '{"token": "token-value"}')
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)

    colab.setup_kaggle()

    assert colab.os.environ["KAGGLE_API_TOKEN"] == "token-value"


def test_setup_kaggle_accepts_legacy_credential_object(monkeypatch):
    monkeypatch.setattr(
        colab, "read_secret", lambda _name: {"username": "kaggle-user", "key": "legacy-key"}
    )
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)

    colab.setup_kaggle()

    assert "KAGGLE_API_TOKEN" not in colab.os.environ
    assert colab.os.environ["KAGGLE_USERNAME"] == "kaggle-user"
    assert colab.os.environ["KAGGLE_KEY"] == "legacy-key"


def test_setup_kaggle_rejects_unrecognized_object_without_leaking_values(monkeypatch):
    secret_value = "do-not-print-this"
    monkeypatch.setattr(colab, "read_secret", lambda _name: {"unexpected": secret_value})

    with pytest.raises(TypeError) as error:
        colab.setup_kaggle()

    assert secret_value not in str(error.value)
