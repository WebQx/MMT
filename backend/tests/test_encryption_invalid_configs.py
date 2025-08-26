import os, base64, json
import pytest

import config as cfg
import persistence

@pytest.fixture(autouse=True)
def clear_settings_cache():
    if hasattr(cfg.get_settings, 'cache_clear'):
        cfg.get_settings.cache_clear()  # type: ignore
    yield


def _rand_key_b64():
    return base64.b64encode(os.urandom(32)).decode()


def test_missing_primary_disables(monkeypatch):
    monkeypatch.setenv('ENABLE_FIELD_ENCRYPTION', 'true')
    k = _rand_key_b64()
    monkeypatch.setenv('ENCRYPTION_KEYS', f'k1:{k}')
    # Intentionally do not set PRIMARY_ENCRYPTION_KEY_ID
    from importlib import reload
    reload(persistence)
    assert persistence.reload_encryption_keys() == 0


def test_duplicate_key_ids(monkeypatch):
    monkeypatch.setenv('ENABLE_FIELD_ENCRYPTION', 'true')
    k = _rand_key_b64()
    # duplicate k1 entries (second should be ignored)
    monkeypatch.setenv('ENCRYPTION_KEYS', f'k1:{k},k1:{k}')
    monkeypatch.setenv('PRIMARY_ENCRYPTION_KEY_ID', 'k1')
    from importlib import reload
    reload(persistence)
    assert persistence.reload_encryption_keys() == 1


def test_invalid_key_length(monkeypatch):
    monkeypatch.setenv('ENABLE_FIELD_ENCRYPTION', 'true')
    bad = base64.b64encode(os.urandom(16)).decode()  # wrong size
    monkeypatch.setenv('ENCRYPTION_KEYS', f'k1:{bad}')
    monkeypatch.setenv('PRIMARY_ENCRYPTION_KEY_ID', 'k1')
    from importlib import reload
    reload(persistence)
    assert persistence.reload_encryption_keys() == 0


def test_legacy_plaintext_roundtrip(monkeypatch):
    # encryption disabled first insert
    if hasattr(cfg.get_settings, 'cache_clear'):
        cfg.get_settings.cache_clear()  # type: ignore
    from importlib import reload
    reload(persistence)
    tid = persistence.store_transcript('f.wav', 'plain text', None, None, 'api')
    assert tid > 0
    rec = persistence.get_transcript(tid)
    assert rec['text'] == 'plain text'
    # Now enable encryption and ensure we can still read
    monkeypatch.setenv('ENABLE_FIELD_ENCRYPTION', 'true')
    k = _rand_key_b64()
    monkeypatch.setenv('ENCRYPTION_KEYS', f'k1:{k}')
    monkeypatch.setenv('PRIMARY_ENCRYPTION_KEY_ID', 'k1')
    if hasattr(cfg.get_settings, 'cache_clear'):
        cfg.get_settings.cache_clear()  # type: ignore
    reload(persistence)
    rec2 = persistence.get_transcript(tid)
    assert rec2['text'] == 'plain text'
