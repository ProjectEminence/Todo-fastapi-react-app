from sqlmodel import select

from app.models.todo_model import Todo


def test_update_with_same_status_value_keeps_other_fields_unchanged(client, session, prefix):
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    todo = Todo(title="Already complete", description="should stay same", status=True, user_id=current_user.id)
    session.add(todo)
    session.commit()
    session.refresh(todo)

    response = client.put(f"{prefix}/todo/{todo.id}", json={"status": True})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(todo.id)
    assert body["status"] is True
    assert body["title"] == "Already complete"
    assert body["description"] == "should stay same"
    assert body["user_id"] == str(current_user.id)

    persisted = session.exec(select(Todo).where(Todo.id == todo.id)).first()
    assert persisted is not None
    assert persisted.status is True
    assert persisted.title == "Already complete"
    assert persisted.description == "should stay same"
