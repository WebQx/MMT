import os
import urllib.parse as _up

import pytest

# We import inside the test after setting env so settings pick up values.

@pytest.mark.parametrize("provider,client_env,base_url,expected_domain", [
    ("google", "OAUTH_GOOGLE_CLIENT_ID", "https://api.example.test", "accounts.google.com"),
    ("microsoft", "OAUTH_MICROSOFT_CLIENT_ID", "https://backend.test", "login.microsoftonline.com"),
])
def test_oauth_authorize_basic(monkeypatch, provider, client_env, base_url, expected_domain):
    monkeypatch.setenv(client_env, f"client-{provider}")
    # front or backend base used to build redirect_uri
    monkeypatch.setenv("OAUTH_BACKEND_BASE_URL", base_url)
    # Clear cached settings so new env vars are read
    import config
    if hasattr(config.get_settings, 'cache_clear'):
        config.get_settings.cache_clear()  # type: ignore[attr-defined]
    from fastapi.testclient import TestClient
    import importlib
    main = importlib.reload(importlib.import_module('main'))
    client = TestClient(main.app)
    r = client.get(f"/auth/oauth/{provider}/authorize")
    assert r.status_code == 200, r.text
    url = r.json()["authorize_url"]
    parsed = _up.urlparse(url)
    assert expected_domain in parsed.netloc
    qs = dict(_up.parse_qsl(parsed.query))
    # Ensure redirect_uri parameter is set correctly
    assert qs.get("redirect_uri").startswith(base_url + f"/auth/oauth/{provider}/callback")
    # Client id presence
    assert qs.get("client_id") == f"client-{provider}"  # provider specific id inserted
    # Basic required params per provider
    if provider == "google":
        assert qs.get("response_type") == "code"
        assert "openid" in qs.get("scope", "")
    if provider == "microsoft":
        assert qs.get("response_type") == "code"
        assert "offline_access" in qs.get("scope", "")


def test_oauth_authorize_google_missing(monkeypatch):
    # Ensure a 400 when google not configured
    import config, importlib
    if hasattr(config.get_settings, 'cache_clear'):
        config.get_settings.cache_clear()  # type: ignore[attr-defined]
    main = importlib.reload(importlib.import_module('main'))
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    r = client.get("/auth/oauth/google/authorize")
    assert r.status_code == 400
    assert "not configured" in r.json()["error"]["message"]


@pytest.mark.skipif(not os.environ.get("OAUTH_APPLE_CLIENT_ID"), reason="Apple client id not provided in env for test")
def test_oauth_authorize_apple(monkeypatch):
    monkeypatch.setenv("OAUTH_APPLE_CLIENT_ID", "apple-client")
    monkeypatch.setenv("OAUTH_BACKEND_BASE_URL", "https://apple.example")
    import config, importlib
    if hasattr(config.get_settings, 'cache_clear'):
        config.get_settings.cache_clear()  # type: ignore[attr-defined]
    main = importlib.reload(importlib.import_module('main'))
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    r = client.get("/auth/oauth/apple/authorize")
    assert r.status_code == 200
    url = r.json()["authorize_url"]
    parsed = _up.urlparse(url)
    assert parsed.netloc == "appleid.apple.com"
    qs = dict(_up.parse_qsl(parsed.query))
    assert qs.get("client_id") == "apple-client"
    assert qs.get("redirect_uri").startswith("https://apple.example/auth/oauth/apple/callback")
