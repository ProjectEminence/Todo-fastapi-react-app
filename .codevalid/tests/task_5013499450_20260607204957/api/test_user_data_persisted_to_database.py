from app.models.user_model import User


def test_user_data_persisted_to_database(client, session, prefix):
    payload = {
        "email": "persist@example.com",
        "username": "persistuser",
        "password": "Pass123!",
        "firstName": "Persist",
        "lastName": "Tester",
        "isAdmin": True,
    }

    response = client.post(f"{prefix}/users/", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "persist@example.com"
    assert body["username"] == "persistuser"
    assert body["firstName"] == "Persist"
    assert body["lastName"] == "Tester"
    assert body["isAdmin"] is True
    assert isinstance(body["id"], str)
    assert body["hashed_password"] != payload["password"]

    stored = session.query(User).filter(User.email == "persist@example.com").first()
    assert stored is not None
    assert stored.email == "persist@example.com"
    assert stored.username == "persistuser"
    assert stored.firstName == "Persist"
    assert stored.lastName == "Tester"
    assert stored.isAdmin is True
    assert stored.hashed_password
    assert stored.hashed_password != payload["password"]
    assert str(stored.id) == body["id"]


def test_user_persistence_creates_single_record(client, session, prefix):
    payload = {
        "email": "persist@example.com",
        "username": "persistuser",
        "password": "Pass123!",
    }

    response = client.post(f"{prefix}/users/", json=payload)
    assert response.status_code == 200

    users = session.query(User).all()
    assert len(users) == 1
    assert users[0].email == "persist@example.com"
    assert users[0].username == "persistuser"
