from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from osint_workbench.api.analyst import router as analyst_router
from osint_workbench.api.cases import router as cases_router
from osint_workbench.api.graph import router as graph_router
from osint_workbench.api.health import router as health_router
from osint_workbench.api.jobs import router as jobs_router
from osint_workbench.api.pivots import router as pivots_router
from osint_workbench.api.intelligence import router as intelligence_router
from osint_workbench.api.reports import router as reports_router
from osint_workbench.api.runs import router as runs_router
from osint_workbench.api.scans import router as scans_router
from osint_workbench.api.system import router as system_router
from osint_workbench.api.ui import WEB_ROOT, router as ui_router


def create_app() -> FastAPI:
    app = FastAPI(title="OSINT Workbench", version="0.7.0")
    app.mount("/ui/static", StaticFiles(directory=WEB_ROOT), name="ui-static")
    app.include_router(health_router)
    app.include_router(system_router)
    app.include_router(analyst_router)
    app.include_router(intelligence_router)
    app.include_router(pivots_router)
    app.include_router(ui_router)
    app.include_router(cases_router)
    app.include_router(graph_router)
    app.include_router(reports_router)
    app.include_router(scans_router)
    app.include_router(jobs_router)
    app.include_router(runs_router)
    return app
