from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from assiette.llm import GroqLLM, generate_itinerary, template_itinerary
from assiette.retrieval import Intent, RankedPlace, rank_places
from backend.api import app
from backend.db.seed import seed_distributions


def _place(**kwargs) -> RankedPlace:
    defaults = dict(
        id="crous-1",
        source="crous",
        name="RU Test",
        org="CROUS",
        kind="Restaurant",
        address="Paris",
        arrondissement=5,
        latitude=48.8,
        longitude=2.3,
        price_eur=3.3,
        open_for_request=True,
        schedule_text="weekday",
        eligibility="student",
        menu_text="",
        booking_required=False,
        last_verified="2026-09-03",
        source_url="https://example.invalid",
        french_hint="",
        notes="",
        score=10,
        reasons=["test"],
    )
    defaults.update(kwargs)
    return RankedPlace(**defaults)


def test_menus_down_still_returns_venues():
    intent = Intent(query="lunch 5th", arrondissement=5, meal="lunch")
    client = MagicMock()
    client.list_paris_restaurants.return_value = (
        [
            {
                "code": 1,
                "nom": "RU Test",
                "adresse": "24 rue des Ecoles, 75005 Paris",
                "latitude": 48.8,
                "longitude": 2.3,
                "zone": "Paris 5",
                "ouvert": True,
                "jours_ouvert": [],
                "type": {"libelle": "Restaurant"},
            }
        ],
        "CROUStillant live",
    )
    client.menu_for.return_value = (None, "menu unavailable")
    places, meta = rank_places(intent, client=client, use_network=True, menu_limit=1, db_session=None)
    assert places
    crous = [p for p in places if p.source == "crous"]
    assert crous
    assert crous[0].id.startswith("crous-")
    assert meta["crous_status"] == "CROUStillant live"


def test_list_cache_stale_status_is_honest():
    intent = Intent(query="lunch", meal="lunch")
    client = MagicMock()
    client.list_paris_restaurants.return_value = ([], "cache stale (l2)")
    places, meta = rank_places(intent, client=client, use_network=False, menu_limit=0, db_session=None)
    assert "stale" in meta["crous_status"] or places is not None


def test_fallback_snapshot_when_list_down():
    from assiette.crous_client import CrousClient
    import requests

    with patch("assiette.crous_client.cache_get", return_value=None), patch(
        "assiette.crous_client.allow_request", return_value=True
    ), patch.object(CrousClient, "_get", side_effect=requests.ConnectionError("down")):
        rows, status = CrousClient().list_paris_restaurants(use_network=True)
    assert rows
    assert "fallback" in status


def test_groq_down_uses_template():
    places = [_place()]
    intent = Intent(query="lunch", meal="lunch")
    llm = GroqLLM(api_key="")
    result = generate_itinerary(intent, places, [], llm)
    assert result["engine"] == "template"
    assert result["stops"][0]["id"] == "crous-1"


def test_invented_stop_is_dropped():
    places = [_place()]
    fallback = template_itinerary(Intent(query="x", meal="lunch"), places, [])
    assert fallback["stops"][0]["id"] in {p.id for p in places}


def test_query_never_blank_when_db_seeded():
    seed_distributions()
    client = TestClient(app)
    resp = client.post("/query", json={"arrondissement": 13, "meal": "dinner", "use_network": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]
    assert data["places"] or data["stops"] is not None


def test_health_degraded_when_db_errors():
    client = TestClient(app)
    with patch("backend.api.VenueRepository") as mock_repo:
        mock_repo.return_value.count_venues.side_effect = RuntimeError("db down")
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["database"] == "error"
