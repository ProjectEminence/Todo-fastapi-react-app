from uuid import UUID

from sqlmodel import select

from app.models.todo_model import Todo


def test_create_todo_partial_data(client, session, prefix):
    response = client.post(
        f"{prefix}/todo/",
        json={"title": "Minimal todo"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Minimal todo"
    assert body["description"] is None
    assert body["status"] is False
    assert isinstance(body["id"], str)
    assert isinstance(body["user_id"], str)
    assert body["created_at"]
    assert body["updated_at"]

    persisted = session.exec(select(Todo).where(Todo.id == UUID(body["id"]))).first()
    assert persisted is not None
    assert persisted.title == "Minimal todo"
    assert persisted.description is None
    assert persisted.status is False

    retrieve_response = client.get(f"{prefix}/todo/{body['id']}")
    assert retrieve_response.status_code == 200
    assert retrieve_response.json() == body
