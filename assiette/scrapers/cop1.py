"""Cop1 Paris distribution page parser."""

from __future__ import annotations

from assiette.geo import arrondissement_from_postal, postal_code_from_text
from assiette.scrapers.base import HtmlScraper, collapse, coords_from_hrefs, parse_time_range, slugify, soup, weekday_from_fr

_IDS = {
    "13ruesanteuil": "cop1-cesure",
    "ruesanteuil": "cop1-cesure",
    "50ruedestournelles": "cop1-mie-bastille",
    "24quaid-austerlitz": "cop1-austerlitz",
    "24quaidausterlitz": "cop1-austerlitz",
}


class Cop1Scraper(HtmlScraper):
    source = "cop1"
    org = "Cop1 Solidarités Étudiantes"
    url = "https://cop1.fr/ville/paris/"
    parser_version = "v1"

    def parse(self, html: str) -> list[dict]:
        rows: list[dict] = []
        for card in soup(html).select(".kl-card-distribution"):
            category = collapse(card.select_one(".kl-cat-distribution").get_text() if card.select_one(".kl-cat-distribution") else "")
            if category and "alimentaire" not in category.lower():
                continue
            days = collapse(card.select_one(".kl-days").get_text() if card.select_one(".kl-days") else "")
            location = collapse(card.select_one(".kl-desc-location").get_text(" ", strip=True) if card.select_one(".kl-desc-location") else "")
            if not location or not arrondissement_from_postal(location):
                continue
            schedule = _schedule_from_days(days)
            street_key = slugify(location.split("750")[0]).replace("-", "")
            venue_id = _IDS.get(street_key) or f"cop1-{slugify(location.split('750')[0])}"
            notes = days if days else "Food and hygiene. Contents vary."
            coords = coords_from_hrefs(card)
            rows.append(
                {
                    "id": venue_id,
                    "name": f"Cop1 at {location.split(',')[0].split('750')[0].strip()}",
                    "org": self.org,
                    "kind": "distribution",
                    "address": location,
                    "arrondissement": arrondissement_from_postal(location),
                    "postal_code": postal_code_from_text(location),
                    "latitude": coords[0] if coords else None,
                    "longitude": coords[1] if coords else None,
                    "price_eur": 0,
                    "eligibility": (
                        "Students with a student card or certificat de scolarité. "
                        "Register for a basket on cop1.fr (Paris)."
                    ),
                    "booking_required": True,
                    "booking_url": self.url,
                    "schedule": schedule,
                    "notes": notes,
                    "french_hint": "Bonjour, je suis inscrit·e pour un panier Cop1. Voici ma carte étudiante.",
                    "source_url": self.url,
                    "source": "distribution",
                }
            )
        return rows


def _schedule_from_days(text: str) -> list[dict]:
    if not text:
        return []
    slot = parse_time_range(text)
    weekday = weekday_from_fr(text)
    if weekday and slot:
        return [{"weekday": weekday, "start": slot[0], "end": slot[1]}]
    return []
