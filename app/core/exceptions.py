from fastapi import Request
from fastapi.responses import JSONResponse


class InsightHubError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"


class ProjectAlreadyExists(InsightHubError):
    status_code = 409
    detail = "Project name already exists"


async def insighthub_exception_handler(request: Request, exc: InsightHubError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
