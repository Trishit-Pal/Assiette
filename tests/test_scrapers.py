from pathlib import Path
from unittest.mock import patch

from assiette.scrapers.base import coords_from_hrefs
from assiette.scrapers.cop1 import Cop1Scraper
from assiette.scrapers.linkee import LinkeeScraper
from backend.db.seed import seed_distributions
from backend.db.session import get_session_factory
from backend.refresh.pipeline import run_pipeline
from backend.repo import VenueRepository

FIXTURES = Path(__file__).parent / "fixtures"


def test_linkee_parser_reads_esspace_monday():
    html = (FIXTURES / "linkee_paris.html").read_text(encoding="utf-8")
    rows = LinkeeScraper().parse(html)
    by_id = {r["id"]: r for r in rows}
    assert "linkee-esspace" in by_id
    esspace = by_id["linkee-esspace"]
    assert esspace["arrondissement"] == 13
    assert esspace["postal_code"] == "75013"
    assert esspace["schedule"][0] == {"weekday": "Monday", "start": "19:30", "end": "21:00"}
    assert len(rows) == 3


def test_cop1_parser_reads_santeuil():
    html = (FIXTURES / "cop1_paris.html").read_text(encoding="utf-8")
    rows = Cop1Scraper().parse(html)
    by_id = {r["id"]: r for r in rows}
    assert "cop1-cesure" in by_id
    assert by_id["cop1-cesure"]["arrondissement"] == 5
    assert by_id["cop1-cesure"]["postal_code"] == "75005"
    assert len(rows) == 2


def test_coords_from_hrefs_parses_google_maps():
    html = '<p><a href="https://www.google.com/maps/@48.83012,2.37654,17z">map</a></p>'
    assert coords_from_hrefs(html) == (48.83012, 2.37654)


def test_scrape_does_not_auto_activate_venues():
    seed_distributions()
    db = get_session_factory()()
    repo = VenueRepository(db)
    before = repo.count_venues()
    linkee_html = (FIXTURES / "linkee_paris.html").read_text(encoding="utf-8")
    cop1_html = (FIXTURES / "cop1_paris.html").read_text(encoding="utf-8")

    def fake_fetch(self):
        return linkee_html if self.source == "linkee" else cop1_html

    try:
        with patch("assiette.scrapers.linkee.LinkeeScraper.fetch", fake_fetch), patch(
            "assiette.scrapers.cop1.Cop1Scraper.fetch", fake_fetch
        ):
            summary = run_pipeline(db, source="scrape")
        after = repo.count_venues()
        pending = repo.count_pending_candidates()
        assert after == before
        assert pending >= 1
        assert "scrape_sources" in summary["stages"]
        ids = {v.id for v in repo.list_active_venues()}
        assert "cop1-18-rue-antoine-bourdelle" not in ids
    finally:
        db.close()


def test_suspect_scrape_skips_age_out():
    seed_distributions()
    db = get_session_factory()()
    try:
        with (
            patch(
                "backend.refresh.pipeline._scrape_sources",
                return_value={"sources": {"linkee": {"rows": 0, "suspect": True}}, "suspect": True},
            ),
            patch("backend.refresh.pipeline._warm_crous", return_value={"restaurants": 0}),
            patch.object(VenueRepository, "age_out_stale") as age,
        ):
            summary = run_pipeline(db, source="all")
        age.assert_not_called()
        assert summary["stages"]["age_out"]["skipped"] is True
        assert summary.get("suspect") is True
    finally:
        db.close()
