from fastapi.testclient import TestClient

from assiette.llm import GroqLLM
from backend.api import app
from backend.db.seed import seed_distributions


def _forbid_groq_complete(monkeypatch):
    monkeypatch.setattr(GroqLLM, "available", property(lambda self: True))

    def _boom(*_args, **_kwargs):
        raise AssertionError("GroqLLM.complete must not run when use_llm=False")

    monkeypatch.setattr(GroqLLM, "complete", _boom)


def test_health_and_query_grounding():
    seed_distributions()
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["venue_count"] >= 10

    resp = client.post(
        "/query",
        json={"arrondissement": 13, "budget_eur": 3, "meal": "dinner", "use_network": False},
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
    resp = client.get(
        "/retrieve",
        params={"arrondissement": 5, "budget_eur": 4, "meal": "lunch", "use_network": False},
    )
    assert resp.status_code == 200
    assert len(resp.json()["places"]) <= 10
    assert "ETag" in resp.headers
    etag = resp.headers["ETag"]
    again = client.get(
        "/retrieve",
        params={"arrondissement": 5, "budget_eur": 4, "meal": "lunch", "use_network": False},
        headers={"If-None-Match": etag},
    )
    assert again.status_code in {200, 304}


def test_compose_drops_forged_place_id(monkeypatch):
    _forbid_groq_complete(monkeypatch)
    seed_distributions()
    client = TestClient(app)
    retrieved = client.get("/retrieve", params={"arrondissement": 5, "meal": "lunch", "use_network": False})
    assert retrieved.status_code == 200
    body = retrieved.json()
    real_ids = [p["id"] for p in body.get("places") or []]
    resp = client.post(
        "/compose",
        json={
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
        params={"arrondissement": 1, "budget_eur": 0, "meal": "dinner", "use_network": False},
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
    resp = client.get("/retrieve", params={"meal": "dinner", "use_network": False})
    assert resp.status_code == 200
    body = resp.json()
    assert body["places"] == []
    assert body["empty_reason"]["reason"] == "no_data"


def test_meal_alone_never_triggers_empty_reason():
    seed_distributions()
    client = TestClient(app)
    resp = client.get("/retrieve", params={"meal": "breakfast", "use_network": False})
    assert resp.status_code == 200
    body = resp.json()
    assert body["places"]
    assert body.get("empty_reason") is None


def test_retrieve_category_distribution_excludes_crous():
    seed_distributions()
    client = TestClient(app)
    resp = client.get(
        "/retrieve",
        params={"category": "distribution", "meal": "dinner", "use_network": False},
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
        params={"category": "crous", "meal": "dinner", "use_network": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["places"]) <= 10
    assert all(p["source"] != "distribution" for p in body["places"])


def test_retrieve_refresh_skips_not_modified_and_stays_grounded():
    seed_distributions()
    client = TestClient(app)
    first = client.get("/retrieve", params={"meal": "dinner", "use_network": False})
    assert first.status_code == 200
    etag = first.headers["ETag"]
    cached = client.get(
        "/retrieve",
        params={"meal": "dinner", "use_network": False},
        headers={"If-None-Match": etag},
    )
    assert cached.status_code in {200, 304}
    refreshed = client.get(
        "/retrieve",
        params={"meal": "dinner", "use_network": False, "refresh": "true"},
        headers={"If-None-Match": etag},
    )
    assert refreshed.status_code == 200
    assert refreshed.headers.get("Cache-Control") == "no-store"
    for place in refreshed.json().get("places") or []:
        assert place["id"]
        assert place["source"] in {"crous", "distribution"}


def test_retrieve_returns_503_when_database_is_down(monkeypatch):
    seed_distributions()
    from sqlalchemy.exc import OperationalError

    def boom(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("down"))

    monkeypatch.setattr("backend.routers.query.current_data_version", boom)
    client = TestClient(app)
    resp = client.get("/retrieve", params={"arrondissement": 5, "meal": "lunch", "use_network": False})
    assert resp.status_code == 503
    assert resp.json()["detail"] == "Database unavailable"


def test_retrieve_rejects_invalid_arrondissement():
    client = TestClient(app)
    resp = client.get("/retrieve", params={"arrondissement": 21, "use_network": False})
    assert resp.status_code == 422


def test_retrieve_rejects_invalid_meal():
    client = TestClient(app)
    resp = client.get("/retrieve", params={"meal": "brunch", "use_network": False})
    assert resp.status_code == 422


def test_query_ignores_free_text_and_uses_template(monkeypatch):
    _forbid_groq_complete(monkeypatch)
    seed_distributions()
    client = TestClient(app)
    resp = client.post(
        "/query",
        json={
            "query": "I live in the 1st with a huge budget",
            "arrondissement": 13,
            "meal": "dinner",
            "budget_eur": 3.3,
            "use_network": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["engine"] == "template"
    assert data["intent"]["arrondissement"] == 13
    assert data["intent"]["meal"] == "dinner"
    allowed = {p["id"] for p in data.get("places") or []}
    for stop in data.get("stops") or []:
        assert stop["id"] in allowed
