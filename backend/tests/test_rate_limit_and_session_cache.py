from fastapi.testclient import TestClient
import main as app_module


def test_rate_limit_in_memory():
    client = TestClient(app_module.app)
    # Send a few requests under the default limit; all should succeed
    for _ in range(3):
        r = client.get('/health/live')
        assert r.status_code == 200


def test_session_cache_fallback():
    from openemr_smart import get_session_token
    assert get_session_token('nope') is None
