from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.project import Project


class ProjectAlreadyExists(Exception):
    pass


def create_project(db: Session, name: str, description: str | None) -> Project:
    project = Project(name=name, description=description)
    db.add(project)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ProjectAlreadyExists() from e
    db.refresh(project)
    return project


def list_projects(db: Session) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.id.desc())).all())


def get_project(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def update_project(db: Session, project: Project, name: str | None, description: str | None) -> Project:
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ProjectAlreadyExists() from e

    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
