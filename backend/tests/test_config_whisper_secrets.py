import importlib

import pytest


@pytest.fixture(autouse=True)
def _restore_settings_cache():
    from config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_openai_key_falls_back_to_whisper_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY_FILE", raising=False)
    monkeypatch.setenv("WHISPER_API_KEY", "whisper-secret")
    monkeypatch.delenv("WHISPER_API_KEY_FILE", raising=False)

    import config as config_module

    importlib.reload(config_module)
    settings = config_module.get_settings()
    assert settings.openai_api_key == "whisper-secret"


def test_openai_key_from_secret_file(monkeypatch, tmp_path):
    secret_file = tmp_path / "openai_key"
    secret_file.write_text("file-secret\n")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(secret_file))
    monkeypatch.delenv("WHISPER_API_KEY", raising=False)
    monkeypatch.delenv("WHISPER_API_KEY_FILE", raising=False)

    import config as config_module

    importlib.reload(config_module)
    settings = config_module.get_settings()
    assert settings.openai_api_key == "file-secret"
