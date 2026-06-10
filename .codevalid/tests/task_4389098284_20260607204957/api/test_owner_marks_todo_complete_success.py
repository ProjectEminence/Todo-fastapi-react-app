import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("SQL_CONNECTION_STRING", "sqlite://")

from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.api.deps.user_deps import get_current_user
from app.database import get_session
from app.main import app
from app.models.todo_model import Todo
from app.models.user_model import User


@pytest.fixture()
def client_and_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    current_user = User(
        id="11111111-1111-1111-1111-111111111111",
        username="currentuser",
        email="currentuser@gmail.com",
        hashed_password="hashed",
    )

    def override_get_session():
        yield session

    async def override_get_current_user():
        return current_user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app, raise_server_exceptions=False)
    try:
        yield client, session, current_user
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_owner_marks_todo_complete_success(client_and_session):
    client, session, current_user = client_and_session

    todo = Todo(
        id="22222222-2222-2222-2222-222222222222",
        title="Finish report",
        description="before standup",
        status=False,
        user_id=current_user.id,
    )
    session.add(todo)
    session.commit()
    session.refresh(todo)

    response = client.put(
        f"/api/v1/todo/{todo.id}",
        json={"status": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(todo.id)
    assert body["title"] == "Finish report"
    assert body["description"] == "before standup"
    assert body["status"] is True
    assert body["user_id"] == str(current_user.id)
    assert "created_at" in body
    assert "updated_at" in body

    persisted = session.get(Todo, todo.id)
    assert persisted is not None
    assert persisted.status is True
    assert persisted.title == "Finish report"
    assert persisted.description == "before standup"
