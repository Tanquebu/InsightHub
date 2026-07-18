from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.routes_auth import router as auth_router
from app.api.v1.routes_datasets import router as datasets_router
from app.api.v1.routes_projects import router as projects_router
from app.core.exceptions import InsightHubError, insighthub_exception_handler
from app.core.logging import configure_logging
from app.core.rate_limit import limiter

configure_logging()

app = FastAPI(title="InsightHub", version="0.1.0")

app.state.limiter = limiter
# slowapi/Starlette's own handler signatures are narrower than Starlette's
# add_exception_handler typeshed stub expects; both handlers work correctly at
# runtime (FastAPI dispatches by registered exception type), so mypy's arg-type
# complaint here is a stub gap, not a real error.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(InsightHubError, insighthub_exception_handler)  # type: ignore[arg-type]


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "insighthub", "version": "v1"}


app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(datasets_router, prefix="/api/v1")
