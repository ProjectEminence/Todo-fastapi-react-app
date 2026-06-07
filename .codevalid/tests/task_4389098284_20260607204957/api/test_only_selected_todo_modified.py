from sqlmodel import select

from app.models.todo_model import Todo


def test_only_selected_todo_modified(client, session, prefix):
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    target = Todo(title="Target", description="to update", status=False, user_id=current_user.id)
    other = Todo(title="Other", description="must stay", status=False, user_id=current_user.id)
    session.add(target)
    session.add(other)
    session.commit()
    session.refresh(target)
    session.refresh(other)

    update_response = client.put(f"{prefix}/todo/{target.id}", json={"status": True})
    assert update_response.status_code == 200
    update_body = update_response.json()
    assert update_body["id"] == str(target.id)
    assert update_body["status"] is True

    other_response = client.get(f"{prefix}/todo/{other.id}")
    assert other_response.status_code == 200
    other_body = other_response.json()
    assert other_body["id"] == str(other.id)
    assert other_body["status"] is False
    assert other_body["title"] == "Other"
    assert other_body["description"] == "must stay"

    target_db = session.exec(select(Todo).where(Todo.id == target.id)).first()
    other_db = session.exec(select(Todo).where(Todo.id == other.id)).first()
    assert target_db is not None and target_db.status is True
    assert other_db is not None and other_db.status is False
