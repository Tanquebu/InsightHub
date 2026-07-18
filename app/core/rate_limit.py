from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Redis-backed, per-IP rate limiter shared by every route (see app/main.py where
# the SlowAPIMiddleware and the RateLimitExceeded handler are registered).
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)
