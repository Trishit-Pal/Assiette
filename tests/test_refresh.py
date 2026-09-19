from backend.refresh.worker import run_refresh


def test_refresh_worker_updates_db():
    summary = run_refresh("linkee")
    assert "updated" in summary or "unchanged" in summary
