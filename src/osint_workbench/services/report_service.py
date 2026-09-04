from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from osint_workbench.services.source_quality import annotate_evidence


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def build_report_from_case(case_dir: str | Path) -> dict:
    case = Path(case_dir)
    meta = _read_json(case / 'meta.json', {})
    evidence = annotate_evidence(_read_json(case / 'evidence.json', []))
    findings = _read_json(case / 'findings.json', [])
    tool_runs = _read_json(case / 'tool_runs.json', [])
    grouped = {'HIGH': [], 'MEDIUM': [], 'LOW': [], 'SEED': []}
    for item in evidence:
        grouped.setdefault(str(item.get('confidence', 'LOW')).upper(), []).append(item)
    independent_families = sorted({family for item in evidence for family in item.get('source_families', [])})
    high_count = len(grouped.get('HIGH', []))
    medium_count = len(grouped.get('MEDIUM', []))
    failed_tools = [run.get('tool','') for run in tool_runs if run.get('status') == 'ERROR']
    executive_summary = [
        f"Zebrano {len(evidence)} elementów evidence: {high_count} HIGH, {medium_count} MEDIUM.",
        f"Niezależne rodziny źródeł: {len(independent_families)}.",
    ]
    if failed_tools:
        executive_summary.append('Błędy narzędzi: ' + ', '.join(x for x in failed_tools if x) + '.')
    else:
        executive_summary.append('Brak zarejestrowanych błędów collectorów.')
    return {
        'case': meta,
        'executive_summary': executive_summary,
        'summary': {
            'evidence_count': len(evidence),
            'finding_count': len(findings),
            'high_count': len(grouped.get('HIGH', [])),
            'medium_count': len(grouped.get('MEDIUM', [])),
            'low_count': len(grouped.get('LOW', [])),
            'independent_source_families': len(independent_families),
        },
        'high': grouped.get('HIGH', []),
        'medium': grouped.get('MEDIUM', []),
        'low': grouped.get('LOW', []),
        'seed': grouped.get('SEED', []),
        'findings': findings,
        'tool_runs': tool_runs,
        'limitations': [
            'Wyniki OSINT wskazują obserwacje i korelacje, a nie automatyczne potwierdzenie tożsamości lub własności zasobu.',
            'Brak wyniku w źródle nie oznacza nieistnienia badanego obiektu.',
        ],
    }


def render_markdown(report: dict) -> str:
    case = report.get('case', {})
    lines = [
        '# OSINT Case Report', '',
        f"- Case ID: {case.get('case_id', '')}",
        f"- Typ: {case.get('type', '')}",
        f"- Cel: {case.get('target', case.get('email', case.get('username', '')))}",
        f"- Tryb: {case.get('mode', '')}",
        f"- Status: {case.get('status', '')}", '',
    ]
    lines.extend(['## Podsumowanie wykonawcze', ''])
    for item in report.get('executive_summary', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append(f"- Niezależne rodziny źródeł: {report.get('summary', {}).get('independent_source_families', 0)}")
    lines.append('')
    for key, title in [('high','HIGH'),('medium','MEDIUM'),('low','LOW')]:
        lines.extend([f'## {title}', ''])
        items = report.get(key, [])
        if not items:
            lines.append('- Brak')
        else:
            for item in items:
                src = ', '.join(item.get('sources', []) or [])
                lines.append(f"- {item.get('type','')}: {item.get('value','')} — źródła: {src}")
        lines.append('')
    lines.extend(['## Narzędzia', ''])
    runs = report.get('tool_runs', [])
    if not runs:
        lines.append('- Brak danych o wykonaniu narzędzi')
    else:
        for run in runs:
            lines.append(f"- {run.get('tool','')}: {run.get('status','')} (exit={run.get('exit_code','')})")
    lines.append('')
    lines.extend(['## Ograniczenia', ''])
    for item in report.get('limitations', []):
        lines.append(f'- {item}')
    lines.append('')
    return '\n'.join(lines)



def _csv_safe(value) -> str:
    """Neutralize spreadsheet formula injection while preserving display value."""
    text = "" if value is None else str(value)

    probe = text.lstrip(" \t\r\n")

    if probe.startswith(("=", "+", "-", "@")):
        return "'" + text

    return text


def render_csv(report: dict) -> str:
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\r\n')
    writer.writerow(['type', 'value', 'confidence', 'sources', 'case_id'])
    case_id = report.get('case', {}).get('case_id', '')
    for level in ('high', 'medium', 'low', 'seed'):
        for item in report.get(level, []):
            writer.writerow([
                _csv_safe(item.get('type', '')),
                _csv_safe(item.get('value', '')),
                _csv_safe(item.get('confidence', '')),
                _csv_safe(','.join(item.get('sources', []) or [])),
                _csv_safe(case_id),
            ])
    return output.getvalue()
