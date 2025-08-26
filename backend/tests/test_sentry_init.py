import os
import importlib

def test_sentry_init_no_crash(monkeypatch):
    os.environ['SENTRY_DSN'] = 'http://example.invalid/1'
    os.environ['FAST_TEST_MODE'] = '1'
    # Force reload main to trigger init
    if 'main' in importlib.sys.modules:
        del importlib.sys.modules['main']
    import main  # noqa: F401
    # If import succeeds, test passes.