from __future__ import annotations

import json
import os
from pathlib import Path


def bind_claims_to_evidence(claims: list[dict], evidence: list[dict]) -> list[dict]:
    known = {str(item.get('id')) for item in evidence if item.get('id')}
    result = []
    for item in claims:
        refs = [str(x) for x in item.get('evidence_ids', []) if str(x) in known]
        result.append({
            **item,
            'evidence_ids': refs,
            'classification': 'SUPPORTED' if refs else 'HYPOTHESIS',
        })
    return result


class AnalystService:
    def __init__(self, provider: str | None = None):
        self.provider = provider or os.environ.get('OSINT_ANALYST_PROVIDER')

    def analyze_case(self, case_dir: str | Path) -> dict:
        case = Path(case_dir)
        try:
            evidence = json.loads((case / 'evidence.json').read_text())
        except Exception:
            evidence = []

        if not self.provider:
            return {'status': 'NOT_CONFIGURED', 'claims': []}

        # Provider adapters are intentionally not enabled in v2 by default.
        # This preserves evidence-bound behavior without sending case data externally.
        return {
            'status': 'NOT_CONFIGURED',
            'provider': self.provider,
            'claims': bind_claims_to_evidence([], evidence),
        }
