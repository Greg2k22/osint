from pathlib import Path

from fastapi.testclient import TestClient

from osint_workbench.app import create_app


WEB = Path("src/osint_workbench/web")


def test_cytoscape_is_vendored_locally():
    vendor = WEB / "vendor" / "cytoscape.min.js"

    assert vendor.exists()
    assert vendor.stat().st_size > 100_000

    html = (WEB / "index.html").read_text()

    assert "/ui/static/vendor/cytoscape.min.js" in html
    assert "unpkg.com/cytoscape" not in html


def test_vendored_cytoscape_is_served():
    client = TestClient(create_app())

    response = client.get("/ui/static/vendor/cytoscape.min.js")

    assert response.status_code == 200
    assert len(response.content) > 100_000
