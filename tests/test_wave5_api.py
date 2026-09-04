from fastapi.testclient import TestClient

from osint_workbench.app import create_app
import osint_workbench.api.system as system_api


def test_system_status_endpoint(monkeypatch):
    monkeypatch.setattr(system_api, 'build_system_status', lambda: {
        'api': 'OK', 'postgres': 'OK', 'redis': 'OK', 'neo4j': 'OK',
        'runner': {'status': 'OK', 'age_seconds': 4}, 'tools': {},
    })
    response = TestClient(create_app()).get('/api/system/status')
    assert response.status_code == 200
    assert response.json()['runner']['status'] == 'OK'
