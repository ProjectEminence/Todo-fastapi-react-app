from uuid import UUID

from sqlmodel import select

from app.models.todo_model import Todo


def test_create_todo_happy_path(client, session, prefix):
    payload = {
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "status": False,
    }

    response = client.post(f"{prefix}/todo/", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "id",
        "title",
        "description",
        "status",
        "created_at",
        "updated_at",
        "user_id",
    }
    assert body["title"] == "Buy groceries"
    assert body["description"] == "Milk, eggs, bread"
    assert body["status"] is False
    assert isinstance(body["id"], str)
    assert isinstance(body["user_id"], str)
    assert body["created_at"]
    assert body["updated_at"]

    persisted = session.exec(select(Todo).where(Todo.id == UUID(body["id"]))).first()
    assert persisted is not None
    assert str(persisted.id) == body["id"]
    assert persisted.title == "Buy groceries"
    assert persisted.description == "Milk, eggs, bread"
    assert persisted.status is False
    assert str(persisted.user_id) == body["user_id"]

    list_response = client.get(f"{prefix}/todo/")
    assert list_response.status_code == 200
    assert list_response.json() == [body]

    retrieve_response = client.get(f"{prefix}/todo/{body['id']}")
    assert retrieve_response.status_code == 200
    assert retrieve_response.json() == body
