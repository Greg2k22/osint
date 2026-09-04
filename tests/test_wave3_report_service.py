import json
from pathlib import Path

from osint_workbench.services.report_service import build_report_from_case, render_markdown, render_csv


def _case(tmp_path: Path) -> Path:
    case = tmp_path / 'case-1'
    case.mkdir()
    (case / 'meta.json').write_text(json.dumps({
        'case_id': 'case-1', 'type': 'DOMAIN', 'target': 'example.org',
        'mode': 'PASSIVE', 'status': 'DONE', 'schema_version': 2,
    }))
    (case / 'evidence.json').write_text(json.dumps([
        {'id': 'ev1', 'type': 'HOST', 'value': 'www.example.org', 'confidence': 'HIGH', 'sources': ['bbot','subfinder','theharvester']},
        {'id': 'ev2', 'type': 'HOST', 'value': 'old.example.org', 'confidence': 'LOW', 'sources': ['bbot']},
    ]))
    (case / 'findings.json').write_text('[]')
    return case


def test_report_groups_evidence_by_confidence(tmp_path):
    report = build_report_from_case(_case(tmp_path))
    assert [x['value'] for x in report['high']] == ['www.example.org']
    assert [x['value'] for x in report['low']] == ['old.example.org']
    assert report['summary']['evidence_count'] == 2


def test_markdown_contains_target_and_limitations(tmp_path):
    text = render_markdown(build_report_from_case(_case(tmp_path)))
    assert '# OSINT Case Report' in text
    assert 'example.org' in text
    assert 'Ograniczenia' in text


def test_csv_escapes_and_has_header(tmp_path):
    case = _case(tmp_path)
    evidence = json.loads((case / 'evidence.json').read_text())
    evidence[0]['value'] = 'host,"quoted".example.org'
    (case / 'evidence.json').write_text(json.dumps(evidence))
    csv_text = render_csv(build_report_from_case(case))
    assert csv_text.startswith('type,value,confidence,sources,case_id\r\n')
    assert '"host,""quoted"".example.org"' in csv_text
