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
        username="optionalviewer",
        email="optionalviewer@example.com",
        firstName="Optional",
        lastName="Viewer",
        isAdmin=False,
        hashed_password="hashed",
    )


def _todo_row(todo_id: str, title: str, user_id: str, description, status):
    return SimpleNamespace(
        id=UUID(todo_id),
        title=title,
        description=description,
        status=status,
        created_at="2024-01-04T00:00:00",
        updated_at="2024-01-04T00:00:00",
        user_id=UUID(user_id),
    )


def test_todo_data_integrity_with_optional_fields_preserves_nullable_and_boolean_values():
    user = _make_user("55555555-5555-5555-5555-555555555555")
    session = RecordingSession(
        [
            _todo_row(
                "dddddddd-dddd-dddd-dddd-ddddddddddd1",
                "Task A",
                str(user.id),
                None,
                False,
            ),
            _todo_row(
                "dddddddd-dddd-dddd-dddd-ddddddddddd2",
                "Task B",
                str(user.id),
                "Details here",
                True,
            ),
        ]
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        assert response.json() == [
            {
                "title": "Task A",
                "description": None,
                "status": False,
                "id": "dddddddd-dddd-dddd-dddd-ddddddddddd1",
                "created_at": "2024-01-04T00:00:00",
                "updated_at": "2024-01-04T00:00:00",
                "user_id": str(user.id),
            },
            {
                "title": "Task B",
                "description": "Details here",
                "status": True,
                "id": "dddddddd-dddd-dddd-dddd-ddddddddddd2",
                "created_at": "2024-01-04T00:00:00",
                "updated_at": "2024-01-04T00:00:00",
                "user_id": str(user.id),
            },
        ]
        assert len(session.statements) == 1
    finally:
        app.dependency_overrides.clear()


def test_todo_data_integrity_with_optional_fields_scopes_query_to_authenticated_user():
    user = _make_user("55555555-5555-5555-5555-555555555555")
    session = RecordingSession([])

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        params = session.statements[0].compile().params
        assert list(params.values()) == [user.id]
    finally:
        app.dependency_overrides.clear()


def test_todo_data_integrity_with_optional_fields_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/todo/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
