from backend.db.seed import seed_distributions
from backend.repo import VenueRepository, venue_to_dict
from backend.db.session import get_session_factory


def test_seed_creates_venues():
    n = seed_distributions()
    assert n >= 10
    db = get_session_factory()()
    try:
        count = VenueRepository(db).count_venues()
        assert count >= 10
    finally:
        db.close()


def test_upsert_venue_persists_postal_code_and_coords():
    db = get_session_factory()()
    try:
        repo = VenueRepository(db)
        venue, _changed = repo.upsert_venue(
            {
                "id": "test-geo",
                "name": "Geo Spot",
                "org": "Test",
                "kind": "distribution",
                "address": "1 rue Test 75013 Paris",
                "arrondissement": 13,
                "postal_code": "75013",
                "latitude": 48.83,
                "longitude": 2.37,
                "price_eur": 0,
                "source": "distribution",
            }
        )
        loaded = repo.get_venue("test-geo")
        assert loaded is not None
        assert loaded.postal_code == "75013"
        assert loaded.latitude == 48.83
        assert loaded.longitude == 2.37
        dumped = venue_to_dict(loaded)
        assert dumped["postal_code"] == "75013"
    finally:
        db.close()


def test_approve_candidate_preserves_scraped_coords_and_postal_code():
    db = get_session_factory()()
    try:
        repo = VenueRepository(db)
        row = repo.upsert_candidate(
            source="linkee",
            org="Linkee",
            venue_id="scraped-geo",
            parser_version="v1",
            content_hash="abc",
            payload={
                "id": "scraped-geo",
                "name": "Scraped Spot",
                "org": "Linkee",
                "kind": "distribution",
                "address": "15 rue Test 75013 Paris",
                "arrondissement": 13,
                "postal_code": "75013",
                "latitude": 48.831,
                "longitude": 2.377,
                "price_eur": 0,
                "source": "distribution",
            },
            diff={},
            status="new",
            commit=True,
        )
        venue = repo.approve_candidate(row.id)
        assert venue.postal_code == "75013"
        assert venue.latitude == 48.831
        assert venue.longitude == 2.377
    finally:
        db.close()
