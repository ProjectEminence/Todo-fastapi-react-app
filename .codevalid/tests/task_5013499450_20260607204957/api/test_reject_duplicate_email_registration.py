from unittest.mock import AsyncMock, patch

from app.services import user_service


def test_reject_duplicate_email_registration(client, prefix):
    payload = {
        "email": "duplicate@example.com",
        "username": "differentuser",
        "password": "NewPass123!",
        "firstName": "Dupe",
        "lastName": "Email",
        "isAdmin": False,
    }

    with patch(
        "app.services.user_service.create_user",
        new=AsyncMock(side_effect=user_service.UserExistsError("email already exists")),
    ) as mock_create:
        response = client.post(f"{prefix}/users/", json=payload)

    assert response.status_code == 409
    body = response.json()
    assert body == {"detail": "email already exists"}
    mock_create.assert_awaited_once()
    called_kwargs = mock_create.await_args.kwargs
    assert called_kwargs["user"].email == "duplicate@example.com"
    assert called_kwargs["user"].username == "differentuser"
    assert called_kwargs["user"].password == "NewPass123!"
    assert called_kwargs["session"] is not None


def test_duplicate_email_with_real_database_returns_409(client, prefix):
    existing = {
        "email": "duplicate@example.com",
        "username": "existinguser",
        "password": "ExistingPass123!",
    }
    duplicate = {
        "email": "duplicate@example.com",
        "username": "differentuser",
        "password": "NewPass123!",
    }

    first = client.post(f"{prefix}/users/", json=existing)
    assert first.status_code == 200

    second = client.post(f"{prefix}/users/", json=duplicate)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]
