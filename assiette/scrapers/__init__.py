"""Org -> scraper map. Only scrapers listed here run in scrape_sources."""

from __future__ import annotations

from assiette.scrapers.cop1 import Cop1Scraper
from assiette.scrapers.linkee import LinkeeScraper

SCRAPERS = {
    "linkee": LinkeeScraper,
    "cop1": Cop1Scraper,
}
