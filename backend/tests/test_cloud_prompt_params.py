import base64
import importlib
from fastapi.testclient import TestClient


class DummyResp:
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self):
        return self._json


def _client(monkeypatch, capture: dict):
    # Patch requests.post before importing main
    import requests  # type: ignore

    def fake_post(url, headers=None, files=None, data=None, timeout=None):  # noqa: D401
        capture['url'] = url
        capture['headers'] = headers
        capture['files'] = files
        capture['data'] = data
        return DummyResp({"text": "mock transcription"})

    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
    monkeypatch.setenv('ENABLE_CLOUD_TRANSCRIPTION', 'true')
    monkeypatch.setenv('ALLOW_GUEST_AUTH', 'true')  # allow guest for write in dev via scope check? still requires write scope
    monkeypatch.setenv('INTERNAL_JWT_SECRET', 'x' * 40)
    monkeypatch.setenv('ENV', 'dev')
    monkeypatch.setenv('ENABLE_LOCAL_TRANSCRIPTION', 'false')

    monkeypatch.setattr(requests, 'post', fake_post)
    import config
    if hasattr(config.get_settings, 'cache_clear'):
        config.get_settings.cache_clear()  # type: ignore[attr-defined]
    import main
    importlib.reload(main)
    return TestClient(main.app)


def test_cloud_inline_audio_with_prompt_and_language(monkeypatch):
    capture = {}
    client = _client(monkeypatch, capture)
    # Provide dummy base64 audio bytes (not a real wav - service doesn't inspect internals here)
    audio_bytes = b'RIFF....WAVEfmt '  # minimal-like header bytes
    audio_b64 = base64.b64encode(audio_bytes).decode()
    payload = {
        'audio_b64': audio_b64,
        'language': 'es',
        'prompt': 'Consulta médica con términos como prescripción',
        'temperature': 0.1,
    }
    # Need auth; simulate by supplying internal token logic bypass? Use guest path not allowed for write; so patch scope requirement by adding role writer in token
    # Simplest: create internal JWT not required because dependency expects Authorization header; we can bypass by monkeypatching get_current_user but easier: set Authorization header variable with bearer test then monkeypatch main.get_current_user.
    import main
    # Override dependency in FastAPI app
    main.app.dependency_overrides[main.get_current_user] = lambda: {'role': 'writer'}
    r = client.post('/transcribe/cloud/', json=payload, headers={'Authorization': 'Bearer test'})
    # cleanup
    main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200, r.text
    assert capture['data']['prompt'].startswith('Consulta')
    assert capture['data']['language'] == 'es'
    assert capture['data']['temperature'] == 0.1


def test_cloud_inline_audio_clamps_temperature_and_auto_language(monkeypatch):
    capture = {}
    client = _client(monkeypatch, capture)
    audio_b64 = base64.b64encode(b'RIFF....WAVEfmt ').decode()
    payload = {
        'audio_b64': audio_b64,
        'language': 'auto',
        'prompt': 'Test prompt',
        'temperature': 5.0,  # out of range -> should clamp to 1.0
    }
    import main
    main.app.dependency_overrides[main.get_current_user] = lambda: {'role': 'writer'}
    r = client.post('/transcribe/cloud/', json=payload, headers={'Authorization': 'Bearer test'})
    main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200
    # language key should be absent due to 'auto'
    assert 'language' not in capture['data']
    assert capture['data']['temperature'] == 1.0
