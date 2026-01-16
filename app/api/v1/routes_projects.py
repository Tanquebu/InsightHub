from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services import projects as project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    try:
        return project_service.create_project(db, payload.name, payload.description)
    except project_service.ProjectAlreadyExists:
        raise HTTPException(status_code=409, detail="Project name already exists")


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return project_service.list_projects(db)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        return project_service.update_project(db, project, payload.name, payload.description)
    except project_service.ProjectAlreadyExists:
        raise HTTPException(status_code=409, detail="Project name already exists")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_service.delete_project(db, project)
    return None
