from unittest.mock import AsyncMock, patch

from app.services import user_service


def test_reject_duplicate_username_registration(client, prefix):
    payload = {
        "email": "newunique@example.com",
        "username": "existinguser",
        "password": "Pass456!",
        "firstName": "Existing",
        "lastName": "Name",
        "isAdmin": False,
    }

    with patch(
        "app.services.user_service.create_user",
        new=AsyncMock(side_effect=user_service.UserExistsError("username already exists")),
    ) as mock_create:
        response = client.post(f"{prefix}/users/", json=payload)

    assert response.status_code == 409
    body = response.json()
    assert body == {"detail": "username already exists"}
    mock_create.assert_awaited_once()
    called_kwargs = mock_create.await_args.kwargs
    assert called_kwargs["user"].email == "newunique@example.com"
    assert called_kwargs["user"].username == "existinguser"
    assert called_kwargs["user"].password == "Pass456!"
    assert called_kwargs["session"] is not None


def test_duplicate_username_with_real_database_returns_409(client, prefix):
    existing = {
        "email": "original@example.com",
        "username": "existinguser",
        "password": "OriginalPass123!",
    }
    duplicate = {
        "email": "newunique@example.com",
        "username": "existinguser",
        "password": "Pass456!",
    }

    first = client.post(f"{prefix}/users/", json=existing)
    assert first.status_code == 200

    second = client.post(f"{prefix}/users/", json=duplicate)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]
