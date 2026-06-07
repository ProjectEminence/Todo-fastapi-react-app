from sqlmodel import select

from app.models.todo_model import Todo


def test_verify_persistence_after_update_with_followup_get(client, session, prefix):
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    todo = Todo(title="Walk dog", description="Evening", status=False, user_id=current_user.id)
    session.add(todo)
    session.commit()
    session.refresh(todo)

    update_response = client.put(f"{prefix}/todo/{todo.id}", json={"status": True})
    assert update_response.status_code == 200
    assert update_response.json()["status"] is True

    get_response = client.get(f"{prefix}/todo/{todo.id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["id"] == str(todo.id)
    assert body["status"] is True
    assert body["title"] == "Walk dog"
    assert body["description"] == "Evening"
    assert body["user_id"] == str(current_user.id)

    persisted = session.exec(select(Todo).where(Todo.id == todo.id)).first()
    assert persisted is not None
    assert persisted.status is True
