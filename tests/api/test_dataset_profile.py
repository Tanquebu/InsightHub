from fastapi.testclient import TestClient

from app.db.models.dataset import Dataset
from app.services import profiling as profiling_service


def _create_project(client: TestClient, name: str = "Alpha") -> dict:
    return client.post("/api/v1/projects", json={"name": name}).json()


def test_get_dataset_profile_returns_persisted_metrics(client: TestClient, db_session, tmp_path):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "sales.csv", "source_type": "upload"},
    ).json()

    csv_path = tmp_path / "sales.csv"
    csv_path.write_text("id,name,amount\n1,Alice,10\n2,Bob,\n3,Carol,30\n")

    db_dataset = db_session.get(Dataset, dataset["id"])
    db_dataset.file_path = str(csv_path)
    db_session.commit()
    profiling_service.profile_dataset(db_session, db_dataset)

    response = client.get(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}/profile"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == dataset["id"]
    assert body["row_count"] == 3
    assert body["column_count"] == 3
    assert body["column_missing_counts"] == {"id": 0, "name": 0, "amount": 1}
    assert body["column_dtypes"]["id"] == "int64"


def test_get_dataset_profile_returns_404_for_missing_dataset(client: TestClient):
    project = _create_project(client)

    response = client.get(
        f"/api/v1/projects/{project['id']}/datasets/999999/profile"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Dataset not found"}


def test_get_dataset_profile_returns_404_when_not_yet_profiled(client: TestClient):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "unprofiled.csv"},
    ).json()

    response = client.get(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}/profile"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Dataset profile not found"}


def test_get_dataset_profile_rejects_dataset_from_another_project(
    client: TestClient, db_session, tmp_path
):
    owner = _create_project(client, "Owner")
    other = _create_project(client, "Other")
    dataset = client.post(
        f"/api/v1/projects/{owner['id']}/datasets",
        json={"name": "private.csv"},
    ).json()

    csv_path = tmp_path / "private.csv"
    csv_path.write_text("a,b\n1,2\n")
    db_dataset = db_session.get(Dataset, dataset["id"])
    db_dataset.file_path = str(csv_path)
    db_session.commit()
    profiling_service.profile_dataset(db_session, db_dataset)

    response = client.get(
        f"/api/v1/projects/{other['id']}/datasets/{dataset['id']}/profile"
    )

    assert response.status_code == 404
