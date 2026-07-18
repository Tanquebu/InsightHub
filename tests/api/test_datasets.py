from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.services import datasets as dataset_service


def _create_project(client: TestClient, name: str = "Alpha") -> dict:
    return client.post("/api/v1/projects", json={"name": name}).json()


def test_create_dataset(client: TestClient):
    project = _create_project(client)
    response = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "sales_2024.csv", "source_type": "upload"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "sales_2024.csv"
    assert body["status"] == "uploaded"
    assert body["project_id"] == project["id"]


def test_create_dataset_with_file_path(client: TestClient):
    project = _create_project(client)
    response = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "sales_2024.csv", "file_path": "/data/sales_2024.csv"},
    )
    assert response.status_code == 201
    assert response.json()["file_path"] == "/data/sales_2024.csv"


def test_update_dataset_file_path(client: TestClient):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "file.csv"},
    ).json()
    assert dataset["file_path"] is None

    response = client.patch(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}",
        json={"file_path": "/data/file.csv"},
    )
    assert response.status_code == 200
    assert response.json()["file_path"] == "/data/file.csv"


def test_create_dataset_project_not_found(client: TestClient):
    response = client.post("/api/v1/projects/999/datasets", json={"name": "file.csv"})
    assert response.status_code == 404


def test_update_dataset_invalid_status_returns_422(client: TestClient):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "file.csv"},
    ).json()
    response = client.patch(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}",
        json={"status": "invalid_status"},
    )
    assert response.status_code == 422


def test_get_dataset_not_found(client: TestClient):
    project = _create_project(client)
    response = client.get(f"/api/v1/projects/{project['id']}/datasets/999")
    assert response.status_code == 404


def test_list_datasets(client: TestClient):
    project = _create_project(client)
    client.post(
        f"/api/v1/projects/{project['id']}/datasets", json={"name": "file_a.csv"}
    )
    client.post(
        f"/api/v1/projects/{project['id']}/datasets", json={"name": "file_b.csv"}
    )
    response = client.get(f"/api/v1/projects/{project['id']}/datasets")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_queue_dataset_ingestion_returns_202_and_marks_pending(client, monkeypatch):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "queued.csv"},
    ).json()
    dispatched: list[int] = []

    def delay(dataset_id: int):
        dispatched.append(dataset_id)
        return SimpleNamespace(id="task-123")

    monkeypatch.setattr(dataset_service.ingest_dataset, "delay", delay)

    response = client.post(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}/ingest"
    )

    assert response.status_code == 202
    assert response.json() == {
        "dataset_id": dataset["id"],
        "status": "pending",
        "task_id": "task-123",
    }
    assert dispatched == [dataset["id"]]
    persisted = client.get(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}"
    ).json()
    assert persisted["status"] == "pending"


def test_queue_dataset_ingestion_rejects_dataset_from_another_project(
    client, monkeypatch
):
    owner = _create_project(client, "Owner")
    other = _create_project(client, "Other")
    dataset = client.post(
        f"/api/v1/projects/{owner['id']}/datasets",
        json={"name": "private.csv"},
    ).json()
    dispatched: list[int] = []
    monkeypatch.setattr(
        dataset_service.ingest_dataset,
        "delay",
        lambda dataset_id: dispatched.append(dataset_id),
    )

    response = client.post(
        f"/api/v1/projects/{other['id']}/datasets/{dataset['id']}/ingest"
    )

    assert response.status_code == 404
    assert dispatched == []


def test_queue_dataset_ingestion_returns_404_for_missing_dataset(client, monkeypatch):
    project = _create_project(client)
    dispatched: list[int] = []
    monkeypatch.setattr(
        dataset_service.ingest_dataset,
        "delay",
        lambda dataset_id: dispatched.append(dataset_id),
    )

    response = client.post(f"/api/v1/projects/{project['id']}/datasets/999999/ingest")

    assert response.status_code == 404
    assert dispatched == []


def test_queue_dataset_ingestion_rejects_duplicate_dispatch(client, monkeypatch):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "once.csv"},
    ).json()
    dispatched: list[int] = []

    def delay(dataset_id: int):
        dispatched.append(dataset_id)
        return SimpleNamespace(id="task-once")

    monkeypatch.setattr(dataset_service.ingest_dataset, "delay", delay)
    endpoint = f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}/ingest"

    assert client.post(endpoint).status_code == 202
    response = client.post(endpoint)

    assert response.status_code == 409
    assert response.json() == {"detail": "Dataset ingestion already started"}
    assert dispatched == [dataset["id"]]


def test_queue_dataset_ingestion_restores_status_when_broker_is_unavailable(
    client, monkeypatch
):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "broker-error.csv"},
    ).json()

    def unavailable(_dataset_id: int):
        raise OSError("broker unavailable")

    monkeypatch.setattr(dataset_service.ingest_dataset, "delay", unavailable)

    response = client.post(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}/ingest"
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Ingestion service unavailable"}
    persisted = client.get(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}"
    ).json()
    assert persisted["status"] == "uploaded"
