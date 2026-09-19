"""Shared helpers for off-request-path HTML scrapers."""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Protocol
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from assiette.circuit import allow_request, record_failure, record_success
from assiette.geo import WEEKDAYS_FR, parse_hhmm
from assiette.http import DEFAULT_TIMEOUT, USER_AGENT, get_session

SCRAPE_UA = f"{USER_AGENT} +https://github.com/assiette"


def slugify(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "")
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    folded = folded.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def format_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_time_range(text: str) -> tuple[str, str] | None:
    parts = re.split(r"\s*(?:à|a|-|–|—)\s*", text, maxsplit=1)
    if len(parts) != 2:
        return None
    start = parse_hhmm(parts[0])
    end = parse_hhmm(parts[1])
    if start is None or end is None:
        return None
    return format_hhmm(start), format_hhmm(end)


def weekday_from_fr(text: str) -> str | None:
    token = slugify(text).split("-")[0]
    return WEEKDAYS_FR.get(token)


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def coords_from_hrefs(html_or_el) -> tuple[float, float] | None:
    """Best-effort lat/lng from a Google Maps (or similar) href. Never geocodes."""
    hrefs: list[str] = []
    if hasattr(html_or_el, "find_all"):
        hrefs = [a.get("href") or "" for a in html_or_el.find_all("a", href=True)]
    else:
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_or_el or "", flags=re.I)
    coord_re = re.compile(
        r"(?:[@]|[?&](?:q|query|ll)=)(-?\d{1,2}\.\d{3,})[,/+](-?\d{1,3}\.\d{3,})"
    )
    for href in hrefs:
        lowered = href.lower()
        if not any(token in lowered for token in ("maps.google", "google.com/maps", "goo.gl", "@")):
            continue
        match = coord_re.search(href)
        if not match:
            continue
        lat, lng = float(match.group(1)), float(match.group(2))
        if 41.0 <= lat <= 51.5 and -5.0 <= lng <= 10.0:
            return lat, lng
    return None


class Scraper(Protocol):
    source: str
    org: str
    url: str
    parser_version: str

    def fetch(self) -> str: ...
    def parse(self, html: str) -> list[dict]: ...


class HtmlScraper:
    source = ""
    org = ""
    url = ""
    parser_version = "v1"
    rate_seconds = 0.4

    def robots_allowed(self) -> bool:
        parsed = urlparse(self.url)
        robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
        parser = RobotFileParser()
        try:
            parser.set_url(robots_url)
            parser.read()
            return parser.can_fetch(SCRAPE_UA, self.url)
        except Exception:
            return True

    def fetch(self) -> str:
        service = f"scrape:{self.source}"
        if not allow_request(service):
            raise RuntimeError(f"{service} circuit open")
        if not self.robots_allowed():
            raise PermissionError(f"robots.txt disallows {self.url}")
        time.sleep(self.rate_seconds)
        try:
            response = get_session().get(
                self.url,
                timeout=DEFAULT_TIMEOUT,
                headers={"User-Agent": SCRAPE_UA, "Accept": "text/html"},
            )
            response.raise_for_status()
            record_success(service)
            return response.text
        except (requests.RequestException, RuntimeError):
            record_failure(service)
            raise

    def parse(self, html: str) -> list[dict]:
        raise NotImplementedError
