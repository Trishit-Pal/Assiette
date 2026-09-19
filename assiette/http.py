"""Shared HTTP session with retries for outbound APIs."""

from __future__ import annotations

import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "Assiette/1.0 (essec-dsba-course-project; non-commercial)"

_lock = threading.Lock()
_session: requests.Session | None = None

CONNECT_READ = tuple[int | float, int | float]

LIST_TIMEOUT: CONNECT_READ = (3, 8)
MENU_TIMEOUT: CONNECT_READ = (3, 5)
GROQ_PARSE_TIMEOUT: CONNECT_READ = (3, 12)
GROQ_GENERATE_TIMEOUT: CONNECT_READ = (3, 20)
DEFAULT_TIMEOUT: CONNECT_READ = (3, 10)


def get_session() -> requests.Session:
    global _session
    if _session is not None:
        return _session
    with _lock:
        if _session is not None:
            return _session
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        retry = Retry(
            total=2,
            connect=2,
            read=1,
            backoff_factor=0.4,
            status_forcelist=(429, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=10)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _session = session
        return session
