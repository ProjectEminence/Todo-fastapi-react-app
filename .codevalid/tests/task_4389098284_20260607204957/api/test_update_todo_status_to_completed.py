import pytest
from sqlmodel import select

from app.models.todo_model import Todo
from app.services import todo_service


def test_update_todo_status_to_completed_via_api(client, session, prefix):
    todo = Todo(title="Buy milk", description="2 liters", status=False, user_id=todo_service.__dict__.get("User", None))
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    todo.user_id = current_user.id
    session.add(todo)
    session.commit()
    session.refresh(todo)

    response = client.put(f"{prefix}/todo/{todo.id}", json={"status": True})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(todo.id)
    assert body["title"] == "Buy milk"
    assert body["description"] == "2 liters"
    assert body["status"] is True
    assert body["user_id"] == str(current_user.id)
    assert "created_at" in body
    assert "updated_at" in body

    persisted = session.exec(select(Todo).where(Todo.id == todo.id)).first()
    assert persisted is not None
    assert persisted.status is True
    assert persisted.title == "Buy milk"
    assert persisted.description == "2 liters"
    assert persisted.user_id == current_user.id
