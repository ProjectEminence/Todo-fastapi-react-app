import pytest

from app.services.todo_service import TodoNotFoundError


def test_update_non_existent_todo_returns_server_error_via_api(client, prefix):
    missing_id = "11111111-1111-1111-1111-111111111111"

    response = client.put(f"{prefix}/todo/{missing_id}", json={"status": True})

    assert response.status_code == 500


def test_update_non_existent_todo_raises_service_error(session, client):
    current_user = client.app.dependency_overrides[next(iter([k for k in client.app.dependency_overrides if k.__name__ == 'get_current_user']))]()
    missing_id = "11111111-1111-1111-1111-111111111111"

    from app.models.todo_model import TodoUpdate
    from app.services.todo_service import update_todo

    with pytest.raises(TodoNotFoundError, match=f"Todo with id {missing_id} not found"):
        import anyio
        anyio.run(update_todo, current_user, missing_id, TodoUpdate(status=True), session)
