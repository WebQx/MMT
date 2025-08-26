import os, importlib, pytest

def _clear_cache():
    import config
    if hasattr(config.get_settings, 'cache_clear'):
        config.get_settings.cache_clear()  # type: ignore


def test_prod_requires_internal_secret(monkeypatch):
    monkeypatch.setenv('ENV', 'prod')
    # ensure no secret is set
    monkeypatch.delenv('INTERNAL_JWT_SECRET', raising=False)
    _clear_cache()
    import config
    with pytest.raises(RuntimeError):
        config.get_settings()


def test_prod_accepts_provided_secret(monkeypatch):
    monkeypatch.setenv('ENV', 'prod')
    monkeypatch.setenv('INTERNAL_JWT_SECRET', 'x'*40)
    _clear_cache()
    import config
    s = config.get_settings()
    assert s.internal_jwt_secret == 'x'*40


def test_prod_rsa_requires_keys(monkeypatch):
    monkeypatch.setenv('ENV', 'prod')
    monkeypatch.setenv('USE_RSA_INTERNAL_JWT', 'true')
    monkeypatch.delenv('INTERNAL_JWT_SECRET', raising=False)
    _clear_cache()
    import config
    with pytest.raises(RuntimeError):
        config.get_settings()

