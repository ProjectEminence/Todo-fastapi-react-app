from sqlmodel import select

from app.models.todo_model import Todo


def test_update_todo_status_to_pending_via_api(client, session, prefix):
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    todo = Todo(
        title="Finish report",
        description="Already done once",
        status=True,
        user_id=current_user.id,
    )
    session.add(todo)
    session.commit()
    session.refresh(todo)

    response = client.put(f"{prefix}/todo/{todo.id}", json={"status": False})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(todo.id)
    assert body["status"] is False
    assert body["title"] == "Finish report"
    assert body["description"] == "Already done once"
    assert body["user_id"] == str(current_user.id)

    persisted = session.exec(select(Todo).where(Todo.id == todo.id)).first()
    assert persisted is not None
    assert persisted.status is False
    assert persisted.title == "Finish report"
    assert persisted.description == "Already done once"
