import os
from unittest.mock import patch

from fastapi.testclient import TestClient


os.environ.setdefault("JWT_SECRET_KEY", "test-access-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("SQL_CONNECTION_STRING", "sqlite:///./test.db")

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_protected_endpoint_rejects_request_without_jwt_token():
    with patch("app.main.create_db_and_tables", return_value=None):
        response = client.post(f"{settings.API_V1_STR}/auth/test-token")

    assert response.status_code == 401
    body = response.json()
    assert body == {"detail": "Not authenticated"}
