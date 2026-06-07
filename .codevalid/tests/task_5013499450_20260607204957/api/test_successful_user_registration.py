import pytest
from app.models.user_model import User


def test_successful_user_registration(client, session, prefix):
    payload = {
        "email": "newuser@example.com",
        "username": "newuser123",
        "password": "SecurePass123!",
        "firstName": "New",
        "lastName": "User",
        "isAdmin": False,
    }

    response = client.post(f"{prefix}/users/", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]
    assert body["firstName"] == payload["firstName"]
    assert body["lastName"] == payload["lastName"]
    assert body["isAdmin"] is False
    assert isinstance(body["id"], str)
    assert "hashed_password" in body
    assert body["hashed_password"]
    assert body["hashed_password"] != payload["password"]

    users = session.query(User).all()
    assert len(users) == 1
    stored = users[0]
    assert str(stored.id) == body["id"]
    assert stored.email == payload["email"]
    assert stored.username == payload["username"]
    assert stored.firstName == payload["firstName"]
    assert stored.lastName == payload["lastName"]
    assert stored.isAdmin is False
    assert stored.hashed_password == body["hashed_password"]
    assert stored.hashed_password != payload["password"]


def test_successful_user_registration_rejects_duplicate_followup(client, prefix):
    first_payload = {
        "email": "newuser@example.com",
        "username": "newuser123",
        "password": "SecurePass123!",
        "firstName": "New",
        "lastName": "User",
        "isAdmin": False,
    }
    second_payload = {
        "email": "newuser@example.com",
        "username": "anotheruser",
        "password": "AnotherPass123!",
        "firstName": "Another",
        "lastName": "User",
        "isAdmin": False,
    }

    first = client.post(f"{prefix}/users/", json=first_payload)
    assert first.status_code == 200

    second = client.post(f"{prefix}/users/", json=second_payload)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]
