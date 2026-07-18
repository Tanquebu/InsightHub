from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.dataset import DatasetCreate, DatasetIngestionOut, DatasetOut, DatasetUpdate
from app.schemas.profile import DatasetProfileOut
from app.services import datasets as dataset_service
from app.services import profiling as profiling_service
from app.services import projects as project_service

router = APIRouter(prefix="/projects/{project_id}/datasets", tags=["Datasets"])


@router.post("", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def create_dataset(project_id: int, payload: DatasetCreate, db: Session = Depends(get_db)):
    if not project_service.get_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return dataset_service.create_dataset(
        db, project_id, payload.name, payload.source_type, payload.file_path
    )


@router.get("", response_model=list[DatasetOut])
def list_datasets(project_id: int, db: Session = Depends(get_db)):
    if not project_service.get_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return dataset_service.list_datasets(db, project_id)


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(project_id: int, dataset_id: int, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset(db, dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post(
    "/{dataset_id}/ingest",
    response_model=DatasetIngestionOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def ingest_dataset(project_id: int, dataset_id: int, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset(db, dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        task_id = dataset_service.queue_ingestion(db, dataset)
    except dataset_service.DatasetIngestionAlreadyStarted:
        raise HTTPException(status_code=409, detail="Dataset ingestion already started")
    except dataset_service.DatasetIngestionDispatchError:
        raise HTTPException(status_code=503, detail="Ingestion service unavailable")

    return {"dataset_id": dataset.id, "status": dataset.status, "task_id": task_id}


@router.get("/{dataset_id}/profile", response_model=DatasetProfileOut)
def get_dataset_profile(project_id: int, dataset_id: int, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset(db, dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = profiling_service.get_dataset_profile(db, dataset_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Dataset profile not found")
    return profile


@router.patch("/{dataset_id}", response_model=DatasetOut)
def update_dataset(project_id: int, dataset_id: int, payload: DatasetUpdate, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset(db, dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset_service.update_dataset(
        db, dataset, payload.name, payload.status, payload.source_type, payload.file_path
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(project_id: int, dataset_id: int, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset(db, dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset_service.delete_dataset(db, dataset)
    return None
