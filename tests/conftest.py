import pytest

from assiette.cache import clear_l1
from backend.config import get_settings
from backend.db.session import get_engine, get_session_factory, init_db


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-which-is-long-enough")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    clear_l1()
    init_db()
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
