from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
_UI = Path(__file__).resolve().parent.parent / "web" / "index.html"


@router.get("/ui", response_class=HTMLResponse)
def ui_dashboard():
    return _UI.read_text(encoding="utf-8")
