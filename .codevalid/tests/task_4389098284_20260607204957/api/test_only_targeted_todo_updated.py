import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("SQL_CONNECTION_STRING", "sqlite://")

from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

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
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    current_user = User(
        id="88888888-8888-8888-8888-888888888888",
        username="multi",
        email="multi@gmail.com",
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


def test_only_targeted_todo_updated(client_and_session):
    client, session, current_user = client_and_session

    target = Todo(
        id="99999999-9999-9999-9999-999999999999",
        title="target",
        description="to complete",
        status=False,
        user_id=current_user.id,
    )
    other = Todo(
        id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        title="other",
        description="should stay pending",
        status=False,
        user_id=current_user.id,
    )
    session.add(target)
    session.add(other)
    session.commit()

    response = client.put(f"/api/v1/todo/{target.id}", json={"status": True})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(target.id)
    assert body["status"] is True
    assert body["title"] == "target"

    target_db = session.get(Todo, target.id)
    other_db = session.get(Todo, other.id)
    assert target_db is not None
    assert other_db is not None
    assert target_db.status is True
    assert other_db.status is False

    list_response = client.get("/api/v1/todo/")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 2
    by_id = {item["id"]: item for item in items}
    assert by_id[str(target.id)]["status"] is True
    assert by_id[str(other.id)]["status"] is False
