from fastapi import FastAPI

from app.api.v1.routes_projects import router as projects_router

app = FastAPI(title="InsightHub", version="0.1.0")

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "insighthub", "version": "v1"}

app.include_router(projects_router, prefix="/api/v1")