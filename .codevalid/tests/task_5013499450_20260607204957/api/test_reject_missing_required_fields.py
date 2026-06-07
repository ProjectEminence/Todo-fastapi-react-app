import pytest
from fastapi import HTTPException

from app.api.api_v1.handlers.user import create_user
from app.models.user_model import UserCreate


@pytest.mark.asyncio
async def test_reject_missing_required_fields_direct_handler_raises_400(session):
    with pytest.raises(HTTPException) as exc_info:
        await create_user(session=session, data=None)

    exc = exc_info.value
    assert exc.status_code == 400
    assert "NoneType" in exc.detail or "has no attribute" in exc.detail


def test_reject_missing_required_fields_http_validation(client, prefix):
    response = client.post(
        f"{prefix}/users/",
        json={"username": "incomplete", "password": "Pass123!"},
    )

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    locs = [entry["loc"][-1] for entry in body["detail"]]
    assert "email" in locs


def test_reject_short_password_http_validation(client, prefix):
    response = client.post(
        f"{prefix}/users/",
        json={"email": "short@example.com", "username": "shorty", "password": "1234"},
    )

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    locs = [entry["loc"][-1] for entry in body["detail"]]
    assert "password" in locs


def test_usercreate_model_requires_password_field():
    with pytest.raises(Exception):
        UserCreate(email="missingpass@example.com", username="nopass")
