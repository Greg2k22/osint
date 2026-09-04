from fastapi.testclient import TestClient
from osint_workbench.app import create_app


def test_ui_has_search_and_related_case_markers():
    client = TestClient(create_app())
    html = client.get("/ui").text
    js = client.get("/ui/static/app.js").text
    assert 'id="case-search"' in html
    assert 'id="related-cases"' in html
    assert "/api/search" in js
    assert "/related" in js
    assert "loadRelatedCases" in js
