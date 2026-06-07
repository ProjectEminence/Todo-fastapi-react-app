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
    def __init__(self, user_id):
        self.id = user_id
        self.username = "token.test"
        self.email = "token@example.com"
        self.firstName = "Token"
        self.lastName = "Tester"
        self.isAdmin = False
        self.hashed_password = "hashed"


client = TestClient(app)


def test_refresh_token_created_with_different_secret():
    user_id = UUID("00000000-0000-0000-0000-000000000055")
    user = DummyUser(user_id)

    with patch("app.main.create_db_and_tables", return_value=None), patch(
        "app.api.auth.jwt.user_service.authenticate", return_value=user
    ):
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={"username": "token.test", "password": "TokenPass123!"},
        )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"access_token", "refresh_token"}

    access_token = body["access_token"]
    refresh_token = body["refresh_token"]

    access_payload = jwt.decode(
        access_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    refresh_payload = jwt.decode(
        refresh_token,
        settings.JWT_REFRESH_SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    assert access_payload["sub"] == str(user_id)
    assert refresh_payload["sub"] == str(user_id)
    assert "exp" in access_payload
    assert "exp" in refresh_payload

    wrong_secret_failed = False
    try:
        jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except jwt.InvalidTokenError:
        wrong_secret_failed = True

    assert wrong_secret_failed is True
