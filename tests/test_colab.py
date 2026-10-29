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
        colab.setup_kaggle(prompt_on_invalid=False)

    assert secret_value not in str(error.value)


def test_invalid_secret_prompts_for_token_without_printing_secrets(monkeypatch, capsys):
    monkeypatch.setattr(colab, "read_secret", lambda _name: {"unexpected": "secret-in-object"})
    prompts = []
    def hidden_input(prompt):
        prompts.append(prompt)
        return " manual-token-value "
    monkeypatch.setattr(colab, "getpass", hidden_input)
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)

    colab.setup_kaggle()

    assert len(prompts) == 1
    assert colab.os.environ["KAGGLE_API_TOKEN"] == "manual-token-value"
    text = capsys.readouterr().out
    assert "secret-in-object" not in text
    assert "manual-token-value" not in text


def test_invalid_secret_accepts_legacy_json_at_hidden_prompt(monkeypatch):
    monkeypatch.setattr(colab, "read_secret", lambda _name: {"unexpected": "hidden"})
    monkeypatch.setattr(colab, "getpass", lambda _prompt: '{"username":"user","key":"key-value"}')
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)

    colab.setup_kaggle()

    assert colab.os.environ["KAGGLE_USERNAME"] == "user"
    assert colab.os.environ["KAGGLE_KEY"] == "key-value"


def test_invalid_replacement_fails_without_leaking_secrets(monkeypatch, capsys):
    monkeypatch.setattr(colab, "read_secret", lambda _name: {"unexpected": "original-secret"})
    monkeypatch.setattr(colab, "getpass", lambda _prompt: '{"wrong":"new-secret"}')
    with pytest.raises(TypeError) as error:
        colab.setup_kaggle()
    assert "new-secret" not in str(error.value)
    assert "original-secret" not in capsys.readouterr().out
