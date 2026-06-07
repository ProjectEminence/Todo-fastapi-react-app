import os
from uuid import UUID
from unittest.mock import patch

from fastapi.testclient import TestClient


os.environ.setdefault("JWT_SECRET_KEY", "test-access-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("SQL_CONNECTION_STRING", "sqlite:///./test.db")

from app.core.config import settings
from app.main import app


class DummyUser:
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email
        self.firstName = "Auth"
        self.lastName = "Tester"
        self.isAdmin = False
        self.hashed_password = "hashed"


client = TestClient(app)


def test_access_token_grants_protected_endpoint_access():
    user_id = UUID("00000000-0000-0000-0000-000000000101")
    login_user = DummyUser(user_id, "auth.test.user", "auth@example.com")
    protected_user = DummyUser(user_id, "auth.test.user", "auth@example.com")

    with patch("app.main.create_db_and_tables", return_value=None), patch(
        "app.api.auth.jwt.user_service.authenticate", return_value=login_user
    ) as mock_auth, patch(
        "app.api.deps.user_deps.user_service.get_user_by_id",
        return_value=protected_user,
    ) as mock_get_user:
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={"username": "auth.test.user", "password": "TestPass789!"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        protected_response = client.post(
            f"{settings.API_V1_STR}/auth/test-token",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert protected_response.status_code == 200
    body = protected_response.json()
    assert body["id"] == str(user_id)
    assert body["username"] == "auth.test.user"
    assert body["email"] == "auth@example.com"
    assert body["firstName"] == "Auth"
    assert body["lastName"] == "Tester"
    assert body["isAdmin"] is False

    mock_auth.assert_called_once()
    mock_get_user.assert_called_once()
    assert mock_get_user.call_args.kwargs["id"] == user_id
    assert "session" in mock_get_user.call_args.kwargs
