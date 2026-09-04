import json
from fastapi.testclient import TestClient

from osint_workbench.app import create_app


def test_report_and_exports_read_case_bundle(tmp_path, monkeypatch):
    case = tmp_path / 'case-a'
    case.mkdir()
    (case / 'meta.json').write_text(json.dumps({'case_id':'case-a','type':'EMAIL','target':'a@example.com','mode':'PASSIVE','status':'DONE'}))
    (case / 'evidence.json').write_text(json.dumps([{'type':'SERVICE_SIGNAL','value':'GitHub','confidence':'LOW','sources':['holehe']}]))
    (case / 'findings.json').write_text('[]')
    monkeypatch.setenv('OSINT_CASES_ROOT', str(tmp_path))
    client = TestClient(create_app())
    assert client.get('/api/cases/case-a/report').status_code == 200
    md = client.get('/api/cases/case-a/report.md')
    assert md.status_code == 200 and 'a@example.com' in md.text
    csv = client.get('/api/cases/case-a/export.csv')
    assert csv.status_code == 200 and 'SERVICE_SIGNAL' in csv.text
    assert client.get('/api/cases/../bad/report').status_code in {400,404}
