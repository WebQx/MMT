import os, sys, base64
os.environ.setdefault('FAST_TEST_MODE','1')
import pytest

# Ensure the backend package directory is on sys.path so tests can `import main`.
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _backend_dir not in sys.path:
	sys.path.insert(0, _backend_dir)

@pytest.fixture
def encryption_env(monkeypatch):
	"""Configure field encryption for a test and reload key material.

	Provides a fresh random 32-byte key each invocation.
	Returns (kid, key_b64).
	"""
	key = os.urandom(32)
	key_b64 = base64.b64encode(key).decode()
	monkeypatch.setenv('ENABLE_FIELD_ENCRYPTION', 'true')
	monkeypatch.setenv('ENCRYPTION_KEYS', f'k1:{key_b64}')
	monkeypatch.setenv('PRIMARY_ENCRYPTION_KEY_ID', 'k1')
	# Clear cached settings so persistence picks up changes
	import config
	if hasattr(config.get_settings, 'cache_clear'):
		config.get_settings.cache_clear()  # type: ignore[attr-defined]
	import persistence
	persistence.reload_encryption_keys()
	return 'k1', key_b64
