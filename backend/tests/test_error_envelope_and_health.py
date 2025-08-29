from fastapi.testclient import TestClient
import os, importlib


def _client_with(feature_env: dict[str,str]):
	for k,v in feature_env.items():
		os.environ[k] = v
	# Clear cached settings before importing main
	import config
	if hasattr(config.get_settings, 'cache_clear'):
		config.get_settings.cache_clear()  # type: ignore[attr-defined]
	import main as app_module
	importlib.reload(app_module)
	return TestClient(app_module.app)


def test_error_envelope_and_health_live():
	import main as app_module
	c = TestClient(app_module.app)
	r = c.get('/health/live')
	assert r.status_code == 200
	# Trigger an error (invalid auth to protected endpoint)
	r2 = c.get('/transcripts/1')
	assert r2.status_code == 401
	body = r2.json()
	assert 'error' in body and 'correlation_id' in body


def test_chart_templates_disabled_returns_404():
	c = _client_with({'ENABLE_CHART_TEMPLATES':'false'})
	r = c.get('/chart/templates')
	assert r.status_code == 404


def test_chart_templates_enabled_flow():
	c = _client_with({'ENABLE_CHART_TEMPLATES':'true'})
	# Guest auth allowed in dev for now to fetch read scope endpoints will still 401
	rt = c.get('/chart/templates')
	assert rt.status_code == 200
	data = rt.json()
	assert 'templates' in data and len(data['templates']) > 0
	# Prompt
	rp = c.get('/chart/prompt/general_soap')
	assert rp.status_code == 200
	assert 'prompt' in rp.json()
	# Parse requires auth -> should 401 without token
	rparse = c.post('/chart/parse', json={'text':'Chief Complaint: cough for 3 days','template_key':'general_soap'})
	assert rparse.status_code == 401
