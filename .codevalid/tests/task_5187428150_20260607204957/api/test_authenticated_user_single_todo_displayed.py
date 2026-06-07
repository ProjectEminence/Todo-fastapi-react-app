from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.deps.user_deps import get_current_user
from app.database import get_session
from app.main import app
from app.models.user_model import User


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class RecordingSession:
    def __init__(self, rows):
        self.rows = rows
        self.statements = []

    def exec(self, statement):
        self.statements.append(statement)
        return FakeResult(self.rows)


def _make_user(user_id: str) -> User:
    return User(
        id=UUID(user_id),
        username="singleviewer",
        email="singleviewer@example.com",
        firstName="Single",
        lastName="Viewer",
        isAdmin=False,
        hashed_password="hashed",
    )


def _todo_row(todo_id: str, title: str, user_id: str):
    return SimpleNamespace(
        id=UUID(todo_id),
        title=title,
        description=None,
        status=False,
        created_at="2024-01-02T00:00:00",
        updated_at="2024-01-02T00:00:00",
        user_id=UUID(user_id),
    )


def test_authenticated_user_single_todo_displayed_returns_one_item():
    user = _make_user("22222222-2222-2222-2222-222222222222")
    session = RecordingSession(
        [
            _todo_row(
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1",
                "Write report",
                str(user.id),
            )
        ]
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        body = response.json()
        assert body == [
            {
                "title": "Write report",
                "description": None,
                "status": False,
                "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1",
                "created_at": "2024-01-02T00:00:00",
                "updated_at": "2024-01-02T00:00:00",
                "user_id": str(user.id),
            }
        ]
        assert len(session.statements) == 1
    finally:
        app.dependency_overrides.clear()


def test_authenticated_user_single_todo_displayed_uses_authenticated_user_filter():
    user = _make_user("22222222-2222-2222-2222-222222222222")
    session = RecordingSession([])

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        assert response.json() == []
        params = session.statements[0].compile().params
        assert list(params.values()) == [user.id]
    finally:
        app.dependency_overrides.clear()


def test_authenticated_user_single_todo_displayed_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/todo/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
