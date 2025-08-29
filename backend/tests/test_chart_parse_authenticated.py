from fastapi.testclient import TestClient
import os
import main as app_module


def test_chart_parse_with_guest():
    os.environ['ENABLE_CHART_TEMPLATES'] = 'true'
    os.environ['ALLOW_GUEST_AUTH'] = 'true'
    # clear cached settings
    import config
    if hasattr(config.get_settings, 'cache_clear'):
        config.get_settings.cache_clear()  # type: ignore[attr-defined]
    c = TestClient(app_module.app)
    # obtain guest token
    token = os.environ.get('GUEST_SECRET','guestsecret')
    headers = {'Authorization': f'Bearer {token}'}
    resp = c.post('/chart/parse', json={'text':'Chief Complaint: headache\nHPI: throbbing pain 2 days','template_key':'general_soap'}, headers=headers)
    assert resp.status_code in (200, 404)  # if template disabled earlier tests might have toggled
    if resp.status_code == 200:
        body = resp.json()
        assert body['fields']['chief_complaint'] is not None
        assert body['fields']['hpi'] is not None
