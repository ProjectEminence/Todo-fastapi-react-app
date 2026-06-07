import time
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
        username="viewer",
        email="viewer@example.com",
        firstName="View",
        lastName="User",
        isAdmin=False,
        hashed_password="hashed",
    )


def _todo_row(todo_id: str, title: str, user_id: str, description=None, status=False):
    return SimpleNamespace(
        id=UUID(todo_id),
        title=title,
        description=description,
        status=status,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        user_id=UUID(user_id),
    )


def test_authenticated_user_multiple_todos_displayed_returns_all_items():
    user = _make_user("11111111-1111-1111-1111-111111111111")
    session = RecordingSession(
        [
            _todo_row(
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
                "Buy groceries",
                str(user.id),
            ),
            _todo_row(
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2",
                "Book flight",
                str(user.id),
            ),
            _todo_row(
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3",
                "Call mom",
                str(user.id),
            ),
        ]
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 3
        assert body == [
            {
                "title": "Buy groceries",
                "description": None,
                "status": False,
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "user_id": str(user.id),
            },
            {
                "title": "Book flight",
                "description": None,
                "status": False,
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "user_id": str(user.id),
            },
            {
                "title": "Call mom",
                "description": None,
                "status": False,
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "user_id": str(user.id),
            },
        ]
        assert len(session.statements) == 1
        compiled = str(session.statements[0])
        assert "FROM todo" in compiled
        assert "todo.user_id" in compiled
    finally:
        app.dependency_overrides.clear()


def test_authenticated_user_multiple_todos_displayed_query_is_scoped_to_authenticated_user():
    user = _make_user("11111111-1111-1111-1111-111111111111")
    session = RecordingSession([])

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        assert response.json() == []
        statement = session.statements[0]
        params = statement.compile().params
        assert list(params.values()) == [user.id]
    finally:
        app.dependency_overrides.clear()


def test_authenticated_user_multiple_todos_displayed_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/todo/")

    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "Not authenticated"
