"""CLI per creare utenti pre-seedati (nessun endpoint di registrazione pubblica).

Uso (dentro il devcontainer / container `api`):

    poetry run python -m app.cli.seed_user --email alice@example.com --password s3cret-passw0rd

Se l'utente esiste già, la password viene aggiornata (utile per resettarla) e
`--inactive` permette di crearlo come disattivato (`is_active=False`).
"""

import argparse

import structlog
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import SessionLocal

log = structlog.get_logger(__name__)


def seed_user(email: str, password: str, is_active: bool = True) -> User:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email, password_hash=hash_password(password), is_active=is_active
            )
            db.add(user)
            action = "user.seed.created"
        else:
            user.password_hash = hash_password(password)
            user.is_active = is_active
            action = "user.seed.updated"

        db.commit()
        db.refresh(user)
        log.info(action, user_id=user.id, email=user.email)
        return user
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crea o aggiorna un utente pre-seedato."
    )
    parser.add_argument("--email", required=True, help="Email/username dell'utente")
    parser.add_argument(
        "--password",
        required=True,
        help="Password in chiaro (verrà hashata con argon2)",
    )
    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Crea l'utente come disattivato (is_active=False)",
    )
    args = parser.parse_args()

    user = seed_user(args.email, args.password, is_active=not args.inactive)
    print(f"OK: user id={user.id} email={user.email} is_active={user.is_active}")


if __name__ == "__main__":
    main()
