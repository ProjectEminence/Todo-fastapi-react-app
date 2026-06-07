from sqlmodel import select

from app.models.todo_model import Todo


def test_create_todo_missing_title(client, session, prefix):
    response = client.post(
        f"{prefix}/todo/",
        json={"description": "Missing title field", "status": False},
    )

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    locs = [error["loc"][-1] for error in body["detail"]]
    assert "title" in locs

    persisted = session.exec(select(Todo)).all()
    assert persisted == []


def test_create_todo_missing_title_does_not_show_up_in_list(client, prefix):
    response = client.get(f"{prefix}/todo/")
    assert response.status_code == 200
    assert response.json() == []
