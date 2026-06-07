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


class DelayedSession:
    def __init__(self, rows, delay_seconds):
        self.rows = rows
        self.delay_seconds = delay_seconds
        self.statements = []

    def exec(self, statement):
        self.statements.append(statement)
        time.sleep(self.delay_seconds)
        return FakeResult(self.rows)


def _make_user(user_id: str) -> User:
    return User(
        id=UUID(user_id),
        username="loadviewer",
        email="loadviewer@example.com",
        firstName="Load",
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
        created_at="2024-01-03T00:00:00",
        updated_at="2024-01-03T00:00:00",
        user_id=UUID(user_id),
    )


def test_loading_state_shown_until_todos_retrieved_waits_for_backend_completion_before_returning():
    user = _make_user("44444444-4444-4444-4444-444444444444")
    session = DelayedSession(
        [
            _todo_row(
                "cccccccc-cccc-cccc-cccc-ccccccccccc1",
                "Prepare slides",
                str(user.id),
            ),
            _todo_row(
                "cccccccc-cccc-cccc-cccc-ccccccccccc2",
                "Join meeting",
                str(user.id),
            ),
        ],
        delay_seconds=0.15,
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            started = time.perf_counter()
            response = client.get("/api/v1/todo/")
            elapsed = time.perf_counter() - started

        assert response.status_code == 200
        assert elapsed >= 0.14
        body = response.json()
        assert len(body) == 2
        assert body[0]["title"] == "Prepare slides"
        assert body[1]["title"] == "Join meeting"
        assert len(session.statements) == 1
    finally:
        app.dependency_overrides.clear()


def test_loading_state_shown_until_todos_retrieved_returns_payload_after_delay():
    user = _make_user("44444444-4444-4444-4444-444444444444")
    session = DelayedSession(
        [
            _todo_row(
                "cccccccc-cccc-cccc-cccc-ccccccccccc1",
                "Prepare slides",
                str(user.id),
            )
        ],
        delay_seconds=0.05,
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: session

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/todo/")

        assert response.status_code == 200
        assert response.json() == [
            {
                "title": "Prepare slides",
                "description": None,
                "status": False,
                "id": "cccccccc-cccc-cccc-cccc-ccccccccccc1",
                "created_at": "2024-01-03T00:00:00",
                "updated_at": "2024-01-03T00:00:00",
                "user_id": str(user.id),
            }
        ]
    finally:
        app.dependency_overrides.clear()


def test_loading_state_shown_until_todos_retrieved_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/todo/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
