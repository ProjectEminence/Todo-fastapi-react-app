from sqlmodel import select

from app.models.todo_model import Todo


def test_create_todo_empty_title(client, session, prefix):
    response = client.post(
        f"{prefix}/todo/",
        json={
            "title": "",
            "description": "Empty title test",
            "status": False,
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    title_errors = [error for error in body["detail"] if error["loc"][-1] == "title"]
    assert title_errors
    assert any(error["type"] in {"value_error.any_str.min_length", "value_error"} for error in title_errors)

    persisted = session.exec(select(Todo)).all()
    assert persisted == []


def test_create_todo_empty_title_keeps_collection_empty(client, prefix):
    list_response = client.get(f"{prefix}/todo/")
    assert list_response.status_code == 200
    assert list_response.json() == []
