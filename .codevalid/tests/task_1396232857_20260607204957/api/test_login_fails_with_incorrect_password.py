import os
from unittest.mock import patch

from fastapi.testclient import TestClient


os.environ.setdefault("JWT_SECRET_KEY", "test-access-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("SQL_CONNECTION_STRING", "sqlite:///./test.db")

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_login_fails_with_incorrect_password():
    with patch("app.main.create_db_and_tables", return_value=None), patch(
        "app.api.auth.jwt.user_service.authenticate", return_value=None
    ) as mock_auth:
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={"username": "jane.smith", "password": "WrongPassword!"},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect email or password"}
    mock_auth.assert_called_once()
    assert mock_auth.call_args.kwargs["username"] == "jane.smith"
    assert mock_auth.call_args.kwargs["password"] == "WrongPassword!"
    assert "session" in mock_auth.call_args.kwargs
