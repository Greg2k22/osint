from osint_workbench.app import create_app


def test_wave5_routes_are_registered():
    paths = set(create_app().openapi()['paths'])
    assert '/api/system/status' in paths
    assert '/api/cases/{case_id}/analysis' in paths
