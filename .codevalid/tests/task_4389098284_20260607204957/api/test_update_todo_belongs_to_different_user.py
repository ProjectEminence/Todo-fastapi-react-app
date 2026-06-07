import pytest
from uuid import uuid4

import anyio
from sqlmodel import select

from app.models.todo_model import Todo, TodoUpdate
from app.models.user_model import User
from app.services.todo_service import TodoNotFoundError, update_todo


def test_update_todo_belongs_to_different_user_service_rejects_update(session, client):
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    other_user = User(
        username="otheruser",
        email="other@example.com",
        firstName="Other",
        lastName="User",
        hashed_password="hashed",
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    foreign_todo = Todo(title="Private", description="belongs elsewhere", status=False, user_id=other_user.id)
    session.add(foreign_todo)
    session.commit()
    session.refresh(foreign_todo)

    with pytest.raises(TodoNotFoundError, match=f"Todo with id {foreign_todo.id} not found"):
        anyio.run(update_todo, current_user, foreign_todo.id, TodoUpdate(status=True), session)

    persisted = session.exec(select(Todo).where(Todo.id == foreign_todo.id)).first()
    assert persisted is not None
    assert persisted.status is False
    assert persisted.user_id == other_user.id


def test_update_todo_belongs_to_different_user_via_api_surfaces_error(client, session, prefix):
    other_user = User(
        username=f"other-{uuid4()}",
        email=f"other-{uuid4()}@example.com",
        firstName="Other",
        lastName="Owner",
        hashed_password="hashed",
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    foreign_todo = Todo(title="Hidden", description="not yours", status=False, user_id=other_user.id)
    session.add(foreign_todo)
    session.commit()
    session.refresh(foreign_todo)

    response = client.put(f"{prefix}/todo/{foreign_todo.id}", json={"status": True})
    assert response.status_code == 500
