import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidCredentials
from app.core.security import verify_password
from app.db.models.user import User

log = structlog.get_logger(__name__)


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentials()

    log.info("user.authenticated", user_id=user.id, email=user.email)
    return user
