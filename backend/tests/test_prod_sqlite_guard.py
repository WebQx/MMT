import importlib, os, importlib.util, sys, types, pytest


def test_sqlite_guard_in_prod(monkeypatch):
    monkeypatch.setenv('ENV', 'prod')
    # Ensure no mysql host so sqlite would be used
    monkeypatch.delenv('TRANSCRIPTS_DB_HOST', raising=False)
    # Reload persistence and expect RuntimeError
    if 'persistence' in sys.modules:
        del sys.modules['persistence']
    with pytest.raises(RuntimeError):
        importlib.import_module('persistence')