from fastapi.testclient import TestClient

from backend.api import app
from backend.db.seed import seed_distributions


def test_health_and_query_grounding():
    seed_distributions()
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["venue_count"] >= 10

    resp = client.post(
        "/query",
        json={"query": "I live in the 13th, euro 3 budget, dinner after 18:00", "use_network": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "data_version" in data
    assert "generated_at" in data
    allowed = {p["id"] for p in data.get("places") or []}
    for stop in data.get("stops") or []:
        assert stop["id"] in allowed


def test_retrieve_is_cacheable():
    seed_distributions()
    client = TestClient(app)
    resp = client.get("/retrieve", params={"q": "lunch in the 5th under 4 euros", "use_network": False})
    assert resp.status_code == 200
    assert len(resp.json()["places"]) <= 10
    assert "ETag" in resp.headers
    etag = resp.headers["ETag"]
    again = client.get(
        "/retrieve",
        params={"q": "lunch in the 5th under 4 euros", "use_network": False},
        headers={"If-None-Match": etag},
    )
    assert again.status_code in {200, 304}


def test_compose_drops_forged_place_id():
    seed_distributions()
    client = TestClient(app)
    retrieved = client.get("/retrieve", params={"q": "lunch 5th", "use_network": False})
    assert retrieved.status_code == 200
    body = retrieved.json()
    real_ids = [p["id"] for p in body.get("places") or []]
    resp = client.post(
        "/compose",
        json={
            "query": "lunch 5th",
            "intent": body.get("intent") or {},
            "place_ids": ["invented-bistro-999", *real_ids[:1]],
            "data_version": body.get("data_version"),
            "use_network": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    for stop in data.get("stops") or []:
        assert stop["id"] != "invented-bistro-999"
        assert stop["id"] in set(real_ids)


def test_auth_request_does_not_leak_eligibility():
    client = TestClient(app)
    unknown = client.post("/auth/request", json={"email": "someone@gmail.com"})
    student = client.post("/auth/request", json={"email": "me@essec.edu"})
    assert unknown.status_code == 200
    assert student.status_code == 200
    assert unknown.json()["message"] == student.json()["message"]
    assert "dev_token" not in unknown.json()
    assert "dev_token" in student.json()


def test_retrieve_endpoint_returns_filters_too_strict_reason(monkeypatch):
    seed_distributions()

    def empty_rank(intent, **kwargs):
        return [], {
            "pre_filter_candidate_count": 10,
            "dropped_by_budget": 7,
            "dropped_by_arrondissement": 3,
            "crous_status": "stub",
        }

    monkeypatch.setattr("backend.services.retrieval_service.rank_places", empty_rank)
    client = TestClient(app)
    resp = client.get(
        "/retrieve",
        params={"q": "dinner", "arrondissement": 1, "budget_eur": 0, "use_network": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["places"] == []
    assert body["empty_reason"]["reason"] == "filters_too_strict"
    assert "budget" in body["empty_reason"]["blocking_chips"]
    assert "arrondissement" in body["empty_reason"]["blocking_chips"]


def test_retrieve_endpoint_returns_no_data_reason_when_sources_empty(monkeypatch):
    seed_distributions()

    def empty_rank(intent, **kwargs):
        return [], {
            "pre_filter_candidate_count": 0,
            "dropped_by_budget": 0,
            "dropped_by_arrondissement": 0,
            "crous_status": "stub",
        }

    monkeypatch.setattr("backend.services.retrieval_service.rank_places", empty_rank)
    client = TestClient(app)
    resp = client.get("/retrieve", params={"q": "dinner in paris", "use_network": False})
    assert resp.status_code == 200
    body = resp.json()
    assert body["places"] == []
    assert body["empty_reason"]["reason"] == "no_data"


def test_meal_alone_never_triggers_empty_reason():
    seed_distributions()
    client = TestClient(app)
    resp = client.get("/retrieve", params={"q": "breakfast somewhere in paris", "use_network": False})
    assert resp.status_code == 200
    body = resp.json()
    assert body["places"]
    assert body.get("empty_reason") is None


def test_retrieve_category_distribution_excludes_crous():
    seed_distributions()
    client = TestClient(app)
    resp = client.get(
        "/retrieve",
        params={"q": "dinner paris", "category": "distribution", "meal": "dinner", "use_network": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["places"]) <= 10
    assert all(p["source"] != "crous" for p in body["places"])


def test_retrieve_category_crous_excludes_distribution():
    seed_distributions()
    client = TestClient(app)
    resp = client.get(
        "/retrieve",
        params={"q": "dinner paris", "category": "crous", "meal": "dinner", "use_network": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["places"]) <= 10
    assert all(p["source"] != "distribution" for p in body["places"])


def test_retrieve_refresh_skips_not_modified_and_stays_grounded():
    seed_distributions()
    client = TestClient(app)
    first = client.get("/retrieve", params={"q": "dinner paris", "use_network": False})
    assert first.status_code == 200
    etag = first.headers["ETag"]
    cached = client.get(
        "/retrieve",
        params={"q": "dinner paris", "use_network": False},
        headers={"If-None-Match": etag},
    )
    assert cached.status_code in {200, 304}
    refreshed = client.get(
        "/retrieve",
        params={"q": "dinner paris", "use_network": False, "refresh": "true"},
        headers={"If-None-Match": etag},
    )
    assert refreshed.status_code == 200
    assert refreshed.headers.get("Cache-Control") == "no-store"
    for place in refreshed.json().get("places") or []:
        assert place["id"]
        assert place["source"] in {"crous", "distribution"}
