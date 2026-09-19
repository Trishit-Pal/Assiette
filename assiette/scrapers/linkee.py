"""Linkee Paris distribution page parser."""

from __future__ import annotations

from assiette.geo import arrondissement_from_postal, postal_code_from_text
from assiette.scrapers.base import HtmlScraper, collapse, coords_from_hrefs, parse_time_range, slugify, soup, weekday_from_fr

_IDS = {
    "esspace": "linkee-esspace",
    "lamaisonbleue": "linkee-maison-bleue",
    "maisonbleue": "linkee-maison-bleue",
    "smartfood": "linkee-smartfood",
}


class LinkeeScraper(HtmlScraper):
    source = "linkee"
    org = "Linkee"
    url = "https://linkee.co/distribution-paris/"
    parser_version = "v1"

    def parse(self, html: str) -> list[dict]:
        blocks = soup(html).select(".et_pb_text_inner")
        rows: list[dict] = []
        weekday: str | None = None
        for block in blocks:
            heading = block.find("h2")
            if heading:
                weekday = weekday_from_fr(heading.get_text(" ", strip=True))
                continue
            strong = block.find("strong")
            if not strong or not weekday:
                continue
            name = collapse(strong.get_text())
            paragraphs = [collapse(p.get_text(" ", strip=True)) for p in block.find_all("p")]
            time_text = next((p for p in paragraphs if parse_time_range(p)), "")
            address = next((p for p in paragraphs if arrondissement_from_postal(p)), "")
            slot = parse_time_range(time_text)
            if not name or not address or slot is None:
                continue
            key = slugify(name).replace("-", "")
            venue_id = _IDS.get(key) or f"linkee-{slugify(name)}"
            coords = coords_from_hrefs(block)
            rows.append(
                {
                    "id": venue_id,
                    "name": f"Linkee at {name}",
                    "org": self.org,
                    "kind": "distribution",
                    "address": address,
                    "arrondissement": arrondissement_from_postal(address),
                    "postal_code": postal_code_from_text(address),
                    "latitude": coords[0] if coords else None,
                    "longitude": coords[1] if coords else None,
                    "price_eur": 0,
                    "eligibility": (
                        "All students. Create a Linkee account, book the distribution, "
                        "bring student card or certificat de scolarité, and a bag. "
                        "One parcel per student per site."
                    ),
                    "booking_required": True,
                    "booking_url": self.url,
                    "schedule": [{"weekday": weekday, "start": slot[0], "end": slot[1]}],
                    "notes": "Rescued produce and staples. Not a plated restaurant meal.",
                    "french_hint": "Bonjour, je viens chercher mon panier Linkee. Voici ma carte étudiante.",
                    "source_url": self.url,
                    "source": "distribution",
                }
            )
        return _merge_schedules(rows)


def _merge_schedules(rows: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for row in rows:
        existing = by_id.get(row["id"])
        if existing is None:
            by_id[row["id"]] = row
            continue
        existing["schedule"] = existing["schedule"] + row["schedule"]
    return list(by_id.values())
