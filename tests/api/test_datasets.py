from fastapi.testclient import TestClient


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
    client.post(f"/api/v1/projects/{project['id']}/datasets", json={"name": "file_a.csv"})
    client.post(f"/api/v1/projects/{project['id']}/datasets", json={"name": "file_b.csv"})
    response = client.get(f"/api/v1/projects/{project['id']}/datasets")
    assert response.status_code == 200
    assert len(response.json()) == 2
