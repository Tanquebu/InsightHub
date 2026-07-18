"""Integration test against the real Postgres instance (service `db`).

Every other test overrides `get_db` with an in-memory SQLite session, so the
actual `app.db.session.SessionLocal` / `get_db` wiring is never exercised by
the rest of the suite. This test hits the real database directly to confirm
the production code path — and the Alembic-migrated schema it depends on —
actually works, complementing the SQLite-based unit tests in test_models.py.

Skipped automatically if no reachable Postgres is configured, so the rest of
the suite still runs offline; CI provides a real `db` service so it runs there.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.dependencies import get_db
from app.db.models.project import Project
from app.db.session import SessionLocal

try:
    with SessionLocal() as _probe:
        _probe.execute(text("SELECT 1"))
    _DB_REACHABLE = True
except OperationalError:
    _DB_REACHABLE = False

pytestmark = pytest.mark.skipif(
    not _DB_REACHABLE, reason="real Postgres instance not reachable"
)


def test_get_db_yields_a_working_session_and_closes_it():
    gen = get_db()
    db = next(gen)
    try:
        assert db.execute(text("SELECT 1")).scalar() == 1
    finally:
        gen.close()


def test_real_schema_round_trip():
    db = SessionLocal()
    project_id = None
    name = f"integration-test-project-{uuid.uuid4()}"
    try:
        project = Project(name=name)
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

        fetched = db.get(Project, project_id)
        assert fetched is not None
        assert fetched.name == name
    finally:
        if project_id is not None:
            leftover = db.get(Project, project_id)
            if leftover is not None:
                db.delete(leftover)
                db.commit()
        db.close()
