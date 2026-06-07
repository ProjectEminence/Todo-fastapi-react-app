from app.api.deps.user_deps import get_current_user
from app.database import get_session
from app.main import app
from sqlmodel import select

from app.models.todo_model import Todo


def test_create_todo_unauthenticated(session, prefix):
    def get_session_override():
        return session

    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = get_session_override

    from fastapi.testclient import TestClient

    with TestClient(app) as unauth_client:
        response = unauth_client.post(
            f"{prefix}/todo/",
            json={
                "title": "Unauthorized task",
                "description": "Should fail",
                "status": False,
            },
        )

    assert response.status_code == 401
    body = response.json()
    assert body == {"detail": "Not authenticated"}

    persisted = session.exec(select(Todo)).all()
    assert persisted == []

    app.dependency_overrides.clear()
