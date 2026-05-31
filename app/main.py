from fastapi import FastAPI

from app.api.v1.routes_datasets import router as datasets_router
from app.api.v1.routes_projects import router as projects_router
from app.core.exceptions import InsightHubError, insighthub_exception_handler
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="InsightHub", version="0.1.0")

app.add_exception_handler(InsightHubError, insighthub_exception_handler)


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "insighthub", "version": "v1"}


app.include_router(projects_router, prefix="/api/v1")
app.include_router(datasets_router, prefix="/api/v1")
