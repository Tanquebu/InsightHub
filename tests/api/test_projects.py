import pytest
from fastapi.testclient import TestClient


def test_create_project(client: TestClient):
    response = client.post("/api/v1/projects", json={"name": "Alpha", "description": "First project"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Alpha"
    assert body["description"] == "First project"
    assert "id" in body


def test_create_project_duplicate_returns_409(client: TestClient):
    client.post("/api/v1/projects", json={"name": "Alpha"})
    response = client.post("/api/v1/projects", json={"name": "Alpha"})
    assert response.status_code == 409


def test_list_projects(client: TestClient):
    client.post("/api/v1/projects", json={"name": "Alpha"})
    client.post("/api/v1/projects", json={"name": "Beta"})
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_project_not_found(client: TestClient):
    response = client.get("/api/v1/projects/999")
    assert response.status_code == 404


def test_delete_project(client: TestClient):
    created = client.post("/api/v1/projects", json={"name": "Alpha"}).json()
    response = client.delete(f"/api/v1/projects/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/projects/{created['id']}").status_code == 404
