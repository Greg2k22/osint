from fastapi.testclient import TestClient

from osint_workbench.app import create_app


def test_ui_uses_external_assets_and_wave4_markers():
    client = TestClient(create_app())
    response = client.get('/ui')
    assert response.status_code == 200
    text = response.text
    assert '/ui/static/app.css' in text
    assert '/ui/static/app.js' in text
    assert '/ui/static/vendor/cytoscape.min.js' in text
    assert 'id="case-graph"' in text
    assert 'id="evidence-panel"' in text
    assert 'id="confidence-high"' in text


def test_ui_static_assets_are_served():
    client = TestClient(create_app())
    css = client.get('/ui/static/app.css')
    js = client.get('/ui/static/app.js')
    assert css.status_code == 200
    assert js.status_code == 200
    assert '#case-graph' in css.text
    assert 'loadCaseGraph' in js.text


def test_ui_keeps_active_authorization_guard_in_browser():
    client = TestClient(create_app())
    js = client.get('/ui/static/app.js').text
    assert "type !== 'DOMAIN'" in js
    assert "active && !authorized" in js


def test_ui_has_case_exports():
    client = TestClient(create_app())
    text = client.get('/ui').text
    assert 'id="export-md"' in text
    assert 'id="export-json"' in text
    assert 'id="export-csv"' in text
