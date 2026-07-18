from fastapi.testclient import TestClient

from app.db.models.dataset import Dataset
from app.services import profiling as profiling_service
from app.services import quality as quality_service


def _create_project(client: TestClient, name: str = "Alpha") -> dict:
    return client.post("/api/v1/projects", json={"name": name}).json()


def _profile_dataset(
    client: TestClient,
    db_session,
    project: dict,
    dataset: dict,
    csv_text: str,
    tmp_path,
):
    csv_path = tmp_path / f"{dataset['id']}.csv"
    csv_path.write_text(csv_text)
    db_dataset = db_session.get(Dataset, dataset["id"])
    db_dataset.file_path = str(csv_path)
    db_session.commit()
    return profiling_service.profile_dataset(db_session, db_dataset)


def test_get_dataset_insights_returns_metrics_and_no_issues_for_clean_data(
    client: TestClient, db_session, tmp_path
):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "clean.csv"},
    ).json()

    profile = _profile_dataset(
        client, db_session, project, dataset, "id,name\n1,Alice\n2,Bob\n", tmp_path
    )
    quality_service.persist_quality_issues(
        db_session, dataset["id"], quality_service.evaluate_quality_rules(profile)
    )

    response = client.get(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}/insights"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == dataset["id"]
    assert body["metrics"]["row_count"] == 2
    assert body["metrics"]["column_count"] == 2
    assert body["metrics"]["total_missing_values"] == 0
    assert body["metrics"]["completeness_score"] == 1.0
    assert body["issues"] == []


def test_get_dataset_insights_returns_persisted_issues_for_dirty_data(
    client: TestClient, db_session, tmp_path
):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "dirty.csv"},
    ).json()

    # 3 of 4 rows missing "name" -> exceeds the critical threshold (0.5).
    profile = _profile_dataset(
        client,
        db_session,
        project,
        dataset,
        "id,name\n1,Alice\n2,\n3,\n4,\n",
        tmp_path,
    )
    quality_service.persist_quality_issues(
        db_session, dataset["id"], quality_service.evaluate_quality_rules(profile)
    )

    response = client.get(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}/insights"
    )

    assert response.status_code == 200
    body = response.json()
    # 3/4 rows missing "name" trips HIGH_MISSING_COLUMN (critical); the same
    # missing data also drags the overall completeness score (0.625) below the
    # default 0.7 threshold, tripping LOW_COMPLETENESS_SCORE too.
    assert len(body["issues"]) == 2
    codes = {issue["rule_code"] for issue in body["issues"]}
    assert codes == {"HIGH_MISSING_COLUMN", "LOW_COMPLETENESS_SCORE"}
    high_missing = next(
        i for i in body["issues"] if i["rule_code"] == "HIGH_MISSING_COLUMN"
    )
    assert high_missing["severity"] == "critical"
    assert "name" in high_missing["message"]
    assert "id" in body["issues"][0]


def test_get_dataset_insights_returns_404_for_missing_dataset(client: TestClient):
    project = _create_project(client)

    response = client.get(f"/api/v1/projects/{project['id']}/datasets/999999/insights")

    assert response.status_code == 404
    assert response.json() == {"detail": "Dataset not found"}


def test_get_dataset_insights_returns_404_when_not_yet_profiled(client: TestClient):
    project = _create_project(client)
    dataset = client.post(
        f"/api/v1/projects/{project['id']}/datasets",
        json={"name": "unprofiled.csv"},
    ).json()

    response = client.get(
        f"/api/v1/projects/{project['id']}/datasets/{dataset['id']}/insights"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Dataset profile not found"}


def test_get_dataset_insights_rejects_dataset_from_another_project(
    client: TestClient, db_session, tmp_path
):
    owner = _create_project(client, "Owner")
    other = _create_project(client, "Other")
    dataset = client.post(
        f"/api/v1/projects/{owner['id']}/datasets",
        json={"name": "private.csv"},
    ).json()

    profile = _profile_dataset(
        client, db_session, owner, dataset, "a,b\n1,2\n", tmp_path
    )
    quality_service.persist_quality_issues(
        db_session, dataset["id"], quality_service.evaluate_quality_rules(profile)
    )

    response = client.get(
        f"/api/v1/projects/{other['id']}/datasets/{dataset['id']}/insights"
    )

    assert response.status_code == 404
