import anyio
from sqlmodel import select

from app.models.todo_model import Todo, TodoUpdate
from app.services.todo_service import update_todo


def test_update_with_empty_data_keeps_todo_unchanged_service_level(session, client):
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    todo = Todo(title="Buy groceries", description="Eggs and bread", status=False, user_id=current_user.id)
    session.add(todo)
    session.commit()
    session.refresh(todo)

    updated = anyio.run(update_todo, current_user, todo.id, TodoUpdate(), session)

    assert updated.id == todo.id
    assert updated.title == "Buy groceries"
    assert updated.description == "Eggs and bread"
    assert updated.status is False
    assert updated.user_id == current_user.id

    persisted = session.exec(select(Todo).where(Todo.id == todo.id)).first()
    assert persisted is not None
    assert persisted.title == "Buy groceries"
    assert persisted.description == "Eggs and bread"
    assert persisted.status is False


def test_update_with_empty_json_keeps_existing_fields_via_api(client, session, prefix):
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    todo = Todo(title="Buy groceries", description="Eggs and bread", status=False, user_id=current_user.id)
    session.add(todo)
    session.commit()
    session.refresh(todo)

    response = client.put(f"{prefix}/todo/{todo.id}", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(todo.id)
    assert body["title"] == "Buy groceries"
    assert body["description"] == "Eggs and bread"
    assert body["status"] is False
    assert body["user_id"] == str(current_user.id)
