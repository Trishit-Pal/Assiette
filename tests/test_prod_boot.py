from backend.config import get_settings
from backend.db.session import _ensure_neon_pooler, _normalise_database_url
from backend.limiter import _storage_uri


def test_normalise_adds_psycopg2_and_drops_channel_binding():
    raw = " postgresql://u:p@ep-x.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require "
    out = _normalise_database_url(raw)
    assert out.startswith("postgresql+psycopg2://")
    assert "channel_binding" not in out
    assert "sslmode=require" in out


def test_neon_direct_host_rewrites_to_pooler():
    url = "postgresql+psycopg2://u:p@ep-green-paper-b1ecqokv.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require"
    pooled = _ensure_neon_pooler(url)
    assert "-pooler." in pooled
    assert pooled == _ensure_neon_pooler(pooled)


def test_storage_uri_falls_back_when_redis_import_fails(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "rediss://default:token@example.upstash.io:6379")
    get_settings.cache_clear()
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "redis" or name.startswith("redis."):
            raise ImportError("No module named redis")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert _storage_uri() == "memory://"
    get_settings.cache_clear()


def test_blank_int_env_vars_use_defaults(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "")
    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "")
    monkeypatch.setenv("SMTP_PORT", "")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.rate_limit_per_minute == 30
    assert settings.trusted_proxy_count == 1
    assert settings.smtp_port == 587
    get_settings.cache_clear()
