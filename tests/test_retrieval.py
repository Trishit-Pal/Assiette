from datetime import datetime

from assiette.geo import arrondissement_from_query, arrondissement_tier, postal_code_from_text, proximity_score
from assiette.llm import generate_itinerary
from assiette.retrieval import DISPLAY_LIMIT, MIN_EXACT_ARRONDISSEMENT_RESULTS, heuristic_intent, rank_places, search_knowledge
from backend.services.retrieval_service import empty_reason_from_meta


MONDAY = datetime(2026, 9, 7, 18, 15)


class StubCrous:
    def __init__(self, restaurants, menus=None):
        self.restaurants = restaurants
        self.menus = menus or {}

    def list_paris_restaurants(self, use_network=True, force=False):
        return self.restaurants, "stub"

    def menu_for(self, code, date=None, use_network=True, force=False):
        return self.menus.get(code, {"data": []}), "stub-menu"


def _crous(arr: int, *, code: int = 1, dinner=True, lunch=True):
    return {
        "code": code,
        "nom": f"RU {arr}e",
        "adresse": f"1 rue Test 75{arr:03d} Paris",
        "latitude": 48.85,
        "longitude": 2.35,
        "ouvert": True,
        "jours_ouvert": [
            {"jour": "Lundi", "ouverture": {"matin": False, "midi": lunch, "soir": dinner}},
        ],
        "zone": f"Paris {arr}",
        "type": {"libelle": "Restaurant"},
    }


def _dist(vid: str, arr: int | None, *, price: float = 0.0, weekday: str = "Monday"):
    return {
        "id": vid,
        "name": vid,
        "org": "Test",
        "kind": "distribution",
        "address": f"1 rue {vid}",
        "arrondissement": arr,
        "price_eur": price,
        "schedule": [{"weekday": weekday, "start": "18:00", "end": "21:00"}],
        "eligibility": "",
        "booking_required": False,
        "last_verified": "2026-09-01",
        "source_url": "",
        "french_hint": "",
        "notes": "",
    }


def test_arrondissement_from_13th_query():
    assert arrondissement_from_query("I live in the 13th, €3 budget, dinner after 18:00") == 13


def test_heuristic_intent_dinner_budget():
    intent = heuristic_intent("I live in the 13th, €3 budget, dinner after 18:00")
    assert intent.arrondissement == 13
    assert intent.budget_eur == 3.0
    assert intent.meal == "dinner"
    assert intent.time_hhmm == "18:00"


def test_heuristic_vegetarian_french():
    intent = heuristic_intent("Je suis végétarien, 5e arrondissement, déjeuner à midi, budget 3,30€")
    assert intent.arrondissement == 5
    assert intent.diet == "vegetarian"
    assert intent.meal == "lunch"
    assert intent.language == "fr"


def test_proximity_same_and_adjacent():
    score, why = proximity_score(13, 13)
    assert score == 40
    assert "same" in why
    adj, _ = proximity_score(14, 13)
    assert adj == 22


def test_knowledge_retrieves_linkee():
    hits = search_knowledge("Linkee basket student card bag")
    assert hits
    assert any("Linkee" in h["title"] or "Linkee" in h["body"] for h in hits)


def test_rank_places_offline_prefers_13th_and_free_for_tight_budget():
    intent = heuristic_intent("I live in the 13th, €3 budget, dinner after 18:00")
    monday = datetime(2026, 9, 7, 18, 15)  # Monday
    places, meta = rank_places(intent, when=monday, use_network=False, menu_limit=0)
    assert places
    assert meta["crous_status"].startswith("fallback") or "CROUStillant" in meta["crous_status"]
    top_ids = [p.id for p in places[:5]]
    assert any(p.arrondissement == 13 for p in places[:4])
    # €3 cannot cover a 3.30 CROUS meal; free Linkee in the 13th should surface.
    assert "linkee-esspace" in top_ids or any(p.price_eur == 0 and p.arrondissement == 13 for p in places[:3])


def test_grounding_rejects_unknown_ids(monkeypatch):
    intent = heuristic_intent("dinner in the 13th")
    places, _ = rank_places(intent, when=datetime(2026, 9, 7, 18, 0), use_network=False, menu_limit=0)
    result = generate_itinerary(intent, places, [])
    allowed = {p.id for p in places[:6]}
    for stop in result["stops"]:
        assert stop["id"] in allowed


def test_postal_code_from_text_and_tier():
    assert postal_code_from_text("15 rue Jean Antoine de Baïf 75013 Paris") == "75013"
    assert arrondissement_tier(13, 13) == "exact"
    assert arrondissement_tier(14, 13) == "nearby"
    assert arrondissement_tier(20, 13) == "out_of_range"
    assert arrondissement_tier(None, 13) == "out_of_range"
    assert arrondissement_tier(13, None) == "unscoped"


def test_rank_places_drops_crous_over_student_budget(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "budget_eur": 3.0, "meal": "dinner"})
    places, meta = rank_places(
        intent, client=StubCrous([_crous(13)]), when=MONDAY, use_network=False, menu_limit=0
    )
    assert places == []
    assert all(p.price_eur <= 3.05 for p in places)
    assert meta["dropped_by_budget"] >= 1


def test_rank_places_keeps_crous_at_bursary_price_when_boursier(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "budget_eur": 1.0, "meal": "dinner", "bursary": True})
    places, _meta = rank_places(
        intent, client=StubCrous([_crous(13)]), when=MONDAY, use_network=False, menu_limit=0
    )
    assert places
    assert all(p.price_eur == 1.0 for p in places)


def test_rank_places_drops_distribution_priced_above_budget(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("paid", 13, price=5.0)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "budget_eur": 0.0, "meal": "dinner"})
    places, meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    assert all(p.id != "paid" for p in places)
    assert meta["dropped_by_budget"] >= 1


def test_rank_places_drops_places_outside_exact_and_adjacent(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {
            "distributions": [_dist("far", 20), _dist("near", 14), _dist("here", 13)],
            "last_compiled": "x",
        },
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, _meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    ids = {p.id for p in places}
    assert "far" not in ids
    assert "here" in ids
    assert all(p.arrondissement in {13, 5, 12, 14} for p in places)


def test_rank_places_exact_tier_marked_and_ranked_first(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {
            "distributions": [_dist("here", 13), _dist("near", 14)],
            "last_compiled": "x",
        },
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    assert places[0].id == "here"
    assert places[0].match.arrondissement == "exact"
    nearby = [p for p in places if p.match.arrondissement == "nearby"]
    assert nearby
    assert meta.get("arrondissement_relaxed_to_nearby")
    assert places.index(next(p for p in places if p.id == "here")) < places.index(
        next(p for p in places if p.id == "near")
    )


def test_rank_places_includes_nearby_when_exact_below_threshold(monkeypatch):
    rows = [_dist("here", 13), _dist("near-a", 14), _dist("near-b", 12)]
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": rows, "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    exact = [p for p in places if p.match.arrondissement == "exact"]
    assert len(exact) < MIN_EXACT_ARRONDISSEMENT_RESULTS
    assert any(p.match.arrondissement == "nearby" for p in places)
    assert meta["arrondissement_relaxed_to_nearby"] is True


def test_rank_places_excludes_nearby_when_exact_meets_threshold(monkeypatch):
    rows = [_dist(f"here-{i}", 13) for i in range(MIN_EXACT_ARRONDISSEMENT_RESULTS)]
    rows.append(_dist("near", 14))
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": rows, "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    assert all(p.match.arrondissement != "nearby" for p in places)
    assert meta["arrondissement_relaxed_to_nearby"] is False


def test_rank_places_drops_unknown_arrondissement_place_when_chip_set(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("ghost", None), _dist("here", 13)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    assert all(p.id != "ghost" for p in places)
    assert meta["dropped_by_arrondissement"] >= 1


def test_rank_places_closed_for_meal_still_returned_with_badge(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, _meta = rank_places(
        intent,
        client=StubCrous([_crous(13, dinner=False, lunch=True)]),
        when=MONDAY,
        use_network=False,
        menu_limit=0,
    )
    assert places
    assert any(p.match.meal == "closed" for p in places)


def test_rank_places_open_ranks_above_closed_within_same_arrondissement(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {
            "distributions": [_dist("open-dist", 13), _dist("closed-dist", 13, weekday="Tuesday")],
            "last_compiled": "x",
        },
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, _meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    ids = [p.id for p in places]
    assert ids.index("open-dist") < ids.index("closed-dist")
    assert next(p for p in places if p.id == "closed-dist").match.meal == "closed"


def test_rank_places_open_nearby_before_closed_exact(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {
            "distributions": [
                _dist("here-closed", 13, weekday="Tuesday"),
                _dist("near-open", 14),
            ],
            "last_compiled": "x",
        },
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, _meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    ids = [p.id for p in places]
    assert ids.index("near-open") < ids.index("here-closed")
    assert next(p for p in places if p.id == "near-open").match.arrondissement == "nearby"
    assert next(p for p in places if p.id == "here-closed").match.arrondissement == "exact"


def test_rank_places_diet_match_does_not_outrank_open(monkeypatch):
    menu = {
        "data": [
            {
                "repas": [
                    {
                        "type": "soir",
                        "categories": [{"libelle": "Plat", "plats": [{"libelle": "tofu végétarien"}]}],
                    }
                ]
            }
        ]
    }
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("open-basket", 13)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner", "diet": "vegetarian"})
    places, _meta = rank_places(
        intent,
        client=StubCrous([_crous(13, code=9, dinner=False)], menus={9: menu}),
        when=MONDAY,
        use_network=False,
        menu_limit=3,
    )
    ids = [p.id for p in places]
    assert ids.index("open-basket") < ids.index("crous-9")
    crous = next(p for p in places if p.id == "crous-9")
    assert crous.match.diet == "match"
    assert crous.match.meal == "closed"


def test_rank_places_diet_match_on_crous_menu_hit(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [], "last_compiled": "x"},
    )
    menu = {
        "data": [
            {
                "repas": [
                    {
                        "type": "soir",
                        "categories": [{"libelle": "Plat", "plats": [{"libelle": "tofu végétarien"}]}],
                    }
                ]
            }
        ]
    }
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner", "diet": "vegetarian"})
    places, _meta = rank_places(
        intent,
        client=StubCrous([_crous(13, code=9)], menus={9: menu}),
        when=MONDAY,
        use_network=False,
        menu_limit=3,
    )
    assert places
    assert places[0].match.diet == "match"


def test_rank_places_distribution_never_diet_filtered_or_dropped(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("basket", 13)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner", "diet": "vegan"})
    places, _meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    assert any(p.id == "basket" for p in places)
    basket = next(p for p in places if p.id == "basket")
    assert basket.match.diet == "not_confirmed"


def test_rank_places_diet_not_applicable_when_chip_unset(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("basket", 13)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, _meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    assert places
    assert all(p.match.diet == "not_applicable" for p in places)


def test_rank_places_meta_counts_drops_by_reason(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("far-paid", 20, price=9.0)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "budget_eur": 0.0, "meal": "dinner"})
    places, meta = rank_places(
        intent, client=StubCrous([_crous(20, code=2)]), when=MONDAY, use_network=False, menu_limit=0
    )
    assert places == []
    assert meta["pre_filter_candidate_count"] >= 1
    assert meta["dropped_by_budget"] + meta["dropped_by_arrondissement"] >= 1


def test_empty_reason_filters_too_strict_from_budget_and_arrondissement():
    reason = empty_reason_from_meta(
        {
            "pre_filter_candidate_count": 10,
            "dropped_by_budget": 6,
            "dropped_by_arrondissement": 4,
        },
        [],
    )
    assert reason is not None
    assert reason.reason == "filters_too_strict"
    assert reason.blocking_chips == ["budget", "arrondissement"]
    assert reason.suggestion == "relax_both"


def test_empty_reason_no_data_when_sources_empty():
    reason = empty_reason_from_meta(
        {
            "pre_filter_candidate_count": 0,
            "dropped_by_budget": 0,
            "dropped_by_arrondissement": 0,
        },
        [],
    )
    assert reason is not None
    assert reason.reason == "no_data"
    assert reason.blocking_chips == []
    assert reason.suggestion is None


def test_meal_mismatch_never_builds_empty_reason(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("evening", 13, weekday="Monday")], "last_compiled": "x"},
    )
    intent = heuristic_intent("breakfast", {"arrondissement": 13, "meal": "breakfast"})
    places, meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    assert places
    assert any(p.match.meal == "closed" for p in places)
    assert empty_reason_from_meta(meta, places) is None


def test_rank_places_caps_at_display_limit(monkeypatch):
    rows = [_dist(f"spot-{i}", 13) for i in range(DISPLAY_LIMIT + 3)]
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": rows, "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner"})
    places, _meta = rank_places(intent, client=StubCrous([]), when=MONDAY, use_network=False, menu_limit=0)
    assert len(places) == DISPLAY_LIMIT


def test_rank_places_category_crous_drops_distributions(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("basket", 13)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner", "category": "crous"})
    places, _meta = rank_places(
        intent,
        client=StubCrous([_crous(13)]),
        when=MONDAY,
        use_network=False,
        menu_limit=0,
    )
    assert places
    assert all(p.source == "crous" for p in places)
    assert all(p.id != "basket" for p in places)


def test_rank_places_category_distribution_drops_crous(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("basket", 13)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner", "category": "distribution"})
    places, _meta = rank_places(
        intent,
        client=StubCrous([_crous(13)]),
        when=MONDAY,
        use_network=False,
        menu_limit=0,
    )
    assert [p.id for p in places] == ["basket"]
    assert all(p.source == "distribution" for p in places)


def test_rank_places_category_any_keeps_both(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {"distributions": [_dist("basket", 13)], "last_compiled": "x"},
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner", "category": "any"})
    places, _meta = rank_places(
        intent,
        client=StubCrous([_crous(13)]),
        when=MONDAY,
        use_network=False,
        menu_limit=0,
    )
    sources = {p.source for p in places}
    assert sources == {"crous", "distribution"}


def test_rank_places_category_filter_keeps_time_first(monkeypatch):
    monkeypatch.setattr(
        "assiette.retrieval.load_distributions",
        lambda **k: {
            "distributions": [_dist("open-dist", 13), _dist("closed-dist", 13, weekday="Tuesday")],
            "last_compiled": "x",
        },
    )
    intent = heuristic_intent("dinner", {"arrondissement": 13, "meal": "dinner", "category": "distribution"})
    places, _meta = rank_places(intent, client=StubCrous([_crous(13)]), when=MONDAY, use_network=False, menu_limit=0)
    ids = [p.id for p in places]
    assert ids.index("open-dist") < ids.index("closed-dist")
    assert all(p.source == "distribution" for p in places)
