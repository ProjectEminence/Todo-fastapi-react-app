import os
from uuid import UUID
from unittest.mock import patch

import jwt
from fastapi.testclient import TestClient


os.environ.setdefault("JWT_SECRET_KEY", "test-access-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("SQL_CONNECTION_STRING", "sqlite:///./test.db")

from app.core.config import settings
from app.main import app


class DummyUser:
    def __init__(self, user_id, username="john.doe", email="john@example.com"):
        self.id = user_id
        self.username = username
        self.email = email
        self.firstName = "John"
        self.lastName = "Doe"
        self.isAdmin = False
        self.hashed_password = "hashed"


client = TestClient(app)


def test_successful_login_with_valid_credentials_returns_jwt_tokens():
    user_id = UUID("00000000-0000-0000-0000-000000000042")
    user = DummyUser(user_id=user_id)

    with patch("app.main.create_db_and_tables", return_value=None), patch(
        "app.api.auth.jwt.user_service.authenticate", return_value=user
    ) as mock_auth:
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={"username": "john.doe", "password": "SecurePass123!"},
        )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"access_token", "refresh_token"}
    assert isinstance(body["access_token"], str)
    assert isinstance(body["refresh_token"], str)
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]

    mock_auth.assert_called_once()
    assert mock_auth.call_args.kwargs["username"] == "john.doe"
    assert mock_auth.call_args.kwargs["password"] == "SecurePass123!"
    assert "session" in mock_auth.call_args.kwargs

    access_payload = jwt.decode(
        body["access_token"],
        settings.JWT_SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    refresh_payload = jwt.decode(
        body["refresh_token"],
        settings.JWT_REFRESH_SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    assert access_payload["sub"] == str(user_id)
    assert refresh_payload["sub"] == str(user_id)
    assert "exp" in access_payload
    assert "exp" in refresh_payload
