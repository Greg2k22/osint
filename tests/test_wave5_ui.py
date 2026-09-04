from fastapi.testclient import TestClient
from osint_workbench.app import create_app


def test_ui_has_system_status_panel():
    client = TestClient(create_app())
    html = client.get('/ui').text
    js = client.get('/ui/static/app.js').text
    assert 'id="system-status-grid"' in html
    assert '/api/system/status' in js
    assert '/ui/static/vendor/cytoscape.min.js' in html
