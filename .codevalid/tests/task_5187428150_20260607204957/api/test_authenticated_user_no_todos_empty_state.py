from uuid import UUID

from fastapi.testclient import TestClient

from app.api.deps.user_deps import get_current_user
from app.database import get_session
from app.main import app
from app.models.user_model import User


class FakeResult:
    def all(self):
        return []


class RecordingSession:
    def __init__(self):
        self.statements = []

    def exec(self, statement):
        self.statements.append(statement)
        return FakeResult()


def _make_user(user_id: str) -> User:
    return User(
        id=UUID(user_id),
        username="emptyviewer",
        email="emptyviewer@example.com",
        firstName="Empty",
        lastName="Viewer",
        isAdmin=False,
        hashed_password="hashed",
    )


def test_authenticated_user_no_todos_empty_state_returns_empty_list():
    user = _make_user("33333333-3333-3333-3333-333333333333")
    session = RecordingSession()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        assert response.json() == []
        assert len(session.statements) == 1
    finally:
        app.dependency_overrides.clear()


def test_authenticated_user_no_todos_empty_state_query_targets_current_user_only():
    user = _make_user("33333333-3333-3333-3333-333333333333")
    session = RecordingSession()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        statement = session.statements[0]
        compiled = str(statement)
        assert "FROM todo" in compiled
        assert "todo.user_id" in compiled
        assert list(statement.compile().params.values()) == [user.id]
    finally:
        app.dependency_overrides.clear()


def test_authenticated_user_no_todos_empty_state_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/todo/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
