from fastapi.testclient import TestClient

from earned_media.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_releases_list():
    r = client.get("/api/releases")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 8
    assert {"release_id", "earned_media_score", "review_queue"} <= set(body[0])


def test_release_report():
    r = client.get("/api/releases/rel-001/report")
    assert r.status_code == 200
    data = r.json()
    assert data["release_id"] == "rel-001"
    assert data["pairs"]
    assert "editorial_label" in data["pairs"][0]


def test_unknown_release_404():
    assert client.get("/api/releases/rel-999/report").status_code == 404


def test_policies():
    r = client.get("/api/policies")
    assert r.status_code == 200
    assert "weights" in r.json()["scoring"]
