from backend.auth import request_magic_link, verify_magic_link
from backend.db.session import get_session_factory
from backend.security.tokens import create_session_token, verify_session_token


def test_session_token_roundtrip():
    db = get_session_factory()()
    try:
        raw = request_magic_link(db, "me@essec.edu")
        assert raw
        user = verify_magic_link(db, raw)
        assert user is not None
        token = create_session_token(user)
        payload = verify_session_token(token)
        assert payload is not None
        assert payload["email"] == "me@essec.edu"
    finally:
        db.close()


def test_session_token_rejects_garbage():
    assert verify_session_token("not-a-token") is None
