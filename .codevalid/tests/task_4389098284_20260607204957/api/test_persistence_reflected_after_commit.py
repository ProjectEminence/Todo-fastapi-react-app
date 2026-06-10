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
        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        username="persist",
        email="persist@gmail.com",
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


def test_persistence_reflected_after_commit(client_and_session):
    client, session, current_user = client_and_session

    todo = Todo(
        id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        title="persist me",
        description="verify with follow-up get",
        status=False,
        user_id=current_user.id,
    )
    session.add(todo)
    session.commit()
    session.refresh(todo)

    update_response = client.put(
        f"/api/v1/todo/{todo.id}",
        json={"status": True},
    )
    assert update_response.status_code == 200
    update_body = update_response.json()
    assert update_body["id"] == str(todo.id)
    assert update_body["status"] is True
    assert update_body["user_id"] == str(current_user.id)

    get_response = client.get(f"/api/v1/todo/{todo.id}")
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["id"] == str(todo.id)
    assert get_body["title"] == "persist me"
    assert get_body["description"] == "verify with follow-up get"
    assert get_body["status"] is True
    assert get_body["user_id"] == str(current_user.id)

    persisted = session.get(Todo, todo.id)
    assert persisted is not None
    assert persisted.status is True
