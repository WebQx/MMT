import os, base64, importlib
import pytest

import config as cfg

def _rand_key():
    return base64.b64encode(os.urandom(32)).decode()

@pytest.fixture(autouse=True)
def clear_cache():
    if hasattr(cfg.get_settings, 'cache_clear'):
        cfg.get_settings.cache_clear()  # type: ignore
    yield


def test_rotation_updates_encrypted_fields(monkeypatch):
    # Initial key k1
    k1 = _rand_key()
    monkeypatch.setenv('ENABLE_FIELD_ENCRYPTION', 'true')
    monkeypatch.setenv('ENCRYPTION_KEYS', f'k1:{k1}')
    monkeypatch.setenv('PRIMARY_ENCRYPTION_KEY_ID', 'k1')
    import persistence
    importlib.reload(persistence)
    persistence.reload_encryption_keys()
    tid = persistence.store_transcript('a.wav', 'rot text', 'rot sum', {'e':'val'}, 'api')
    assert tid > 0
    # Add new key k2 make it primary
    k2 = _rand_key()
    monkeypatch.setenv('ENCRYPTION_KEYS', f'k1:{k1},k2:{k2}')
    monkeypatch.setenv('PRIMARY_ENCRYPTION_KEY_ID', 'k2')
    if hasattr(cfg.get_settings, 'cache_clear'):
        cfg.get_settings.cache_clear()  # type: ignore
    importlib.reload(persistence)
    persistence.reload_encryption_keys()
    updated = persistence.rotate_encryption_keys(batch_size=100, max_batches=2)
    assert updated >= 1
    rec = persistence.get_transcript(tid)
    assert rec['text'] == 'rot text'
    assert rec['summary'] == 'rot sum'
    assert rec['enrichment']['e'] == 'val'
