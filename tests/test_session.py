from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from backend.db import session as session_mod


def test_get_db_rolls_back_on_consumer_exception(monkeypatch):
    db = MagicMock()
    factory = MagicMock(return_value=db)
    monkeypatch.setattr(session_mod, "get_session_factory", lambda: factory)

    gen = session_mod.get_db()
    assert next(gen) is db
    with pytest.raises(OperationalError):
        gen.throw(OperationalError("stmt", {}, Exception("aborted")))
    db.rollback.assert_called_once()
    db.close.assert_called_once()
