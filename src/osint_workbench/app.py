from fastapi import FastAPI
from osint_workbench.api.cases import router as cases_router
from osint_workbench.api.health import router as health_router
from osint_workbench.api.graph import router as graph_router
from osint_workbench.api.reports import router as reports_router
from osint_workbench.api.jobs import router as jobs_router
from osint_workbench.api.runs import router as runs_router
from osint_workbench.api.scans import router as scans_router
from osint_workbench.api.ui import router as ui_router


def create_app() -> FastAPI:
    app = FastAPI(title="OSINT Workbench", version="0.2.0")
    app.include_router(health_router)
    app.include_router(ui_router)
    app.include_router(cases_router)
    app.include_router(graph_router)
    app.include_router(reports_router)
    app.include_router(scans_router)
    app.include_router(jobs_router)
    app.include_router(runs_router)
    return app
