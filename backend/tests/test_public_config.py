import os
import json
from fastapi.testclient import TestClient

# Ensure test mode to skip heavy model load
os.environ['FAST_TEST_MODE'] = '1'

from main import app  # noqa: E402

def test_public_config_endpoint():
    client = TestClient(app)
    r = client.get('/config/public')
    assert r.status_code == 200, r.text
    data = r.json()
    assert 'version' in data
    assert 'environment' in data or 'env' in data
    assert 'features' in data
    feats = data['features']
    for key in ['cloud_transcription','local_transcription','partial_streaming','chart_templates']:
        assert key in feats
    assert 'limits' in data and 'max_upload_bytes' in data['limits']


def test_version_endpoint():
    client = TestClient(app)
    r = client.get('/version')
    assert r.status_code == 200
    v = r.json()
    assert 'version' in v and 'demo_mode' in v
