from osint_workbench.app import create_app


def test_wave3_routes_are_exposed():
    paths = set(create_app().openapi()['paths'])
    assert '/api/cases/{case_id}/graph' in paths
    assert '/api/cases/{case_id}/report' in paths
    assert '/api/cases/{case_id}/report.md' in paths
    assert '/api/cases/{case_id}/export.json' in paths
    assert '/api/cases/{case_id}/export.csv' in paths
