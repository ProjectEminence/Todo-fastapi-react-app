from uuid import UUID

from sqlmodel import select

from app.models.todo_model import Todo


def test_create_todo_persistence_verified(client, session, prefix):
    response = client.post(
        f"{prefix}/todo/",
        json={
            "title": "Persistence test",
            "description": "Verify DB storage",
            "status": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    todo_id = UUID(body["id"])

    persisted = session.exec(select(Todo).where(Todo.id == todo_id)).first()
    assert persisted is not None
    assert str(persisted.id) == body["id"]
    assert persisted.title == "Persistence test"
    assert persisted.description == "Verify DB storage"
    assert persisted.status is True
    assert str(persisted.user_id) == body["user_id"]

    all_rows = session.exec(select(Todo)).all()
    assert len(all_rows) == 1
    assert str(all_rows[0].id) == body["id"]
