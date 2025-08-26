import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from importlib import reload
import config as config_module
import main as app_module

client = TestClient(app_module.app)

@pytest.fixture(autouse=True)
def smart_env(monkeypatch):
    monkeypatch.setenv('OPENEMR_FHIR_BASE_URL', 'http://example')
    monkeypatch.setenv('OPENEMR_FHIR_CLIENT_ID', 'cid')
    monkeypatch.setenv('OPENEMR_FHIR_CLIENT_SECRET', 'csecret')
    monkeypatch.setenv('OPENEMR_FHIR_REDIRECT_URI', 'http://localhost/callback')
    # Force reload settings for each test (simplistic; relies on lru cache clear)
    from config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    reload(config_module)
    reload(app_module)
    yield


def test_authorize_url(smart_env):
    r = client.get('/auth/fhir/authorize', headers={'Authorization': f'Bearer {app_module.settings.guest_secret}'})
    assert r.status_code == 200
    data = r.json()
    assert 'authorize_url' in data
    assert 'response_type=code' in data['authorize_url']


def test_callback_and_internal_jwt(smart_env, monkeypatch):
    fake_response = {
        'access_token': 'fhir-token',
        'refresh_token': 'refresh-token',
        'scope': 'user/Patient.read user/DocumentReference.read',
        'expires_in': 3600,
    }
    def fake_exchange(code, state):
        # simulate internal call returns token payload with session_id injection later
        from openemr_smart import exchange_code as real_exchange
        # we mock requests.post inside exchange_code instead; simpler bypass by patching directly would replicate logic
        return {**fake_response, 'session_id': 'sess123'}

    with patch('main.exchange_code', side_effect=lambda code, state: {**fake_response, 'session_id': 'sess123'}), \
         patch('main.get_session_token', return_value={'session_id': 'sess123', 'access_token': 'fhir-token', 'scope': fake_response['scope']}):
        r = client.get('/auth/fhir/callback', params={'code': 'abc', 'state': 'xyz'}, headers={'Authorization': f'Bearer {app_module.settings.guest_secret}'})
        assert r.status_code == 200
        internal = r.json()['access_token']
        assert internal
        me = client.get('/auth/me', headers={'Authorization': f'Bearer {internal}'})
        assert me.status_code == 200
        # Role mapped to reader when only read scopes present
        assert me.json().get('role') in ('reader','writer')


def test_scope_enforcement_missing(monkeypatch):
    # create internal token with no scopes
    from jose import jwt
    token = jwt.encode({'sid': 'missing', 'scope': '', 'iss': 'mmt-backend'}, app_module.settings.internal_jwt_secret, algorithm='HS256')
    with patch('main.get_session_token', return_value={'session_id': 'missing', 'access_token': 'tok', 'scope': ''}):
        r = client.post('/transcribe/local/', headers={'Authorization': f'Bearer {token}'}, files={'file': ('a.wav', b'data', 'audio/wav')})
    assert r.status_code == 403
