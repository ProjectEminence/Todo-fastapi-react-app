def test_create_todo_ui_visibility(client, prefix):
    response = client.post(
        f"{prefix}/todo/",
        json={
            "title": "UI Display Test",
            "description": "Immediate visibility",
            "status": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "id",
        "title",
        "description",
        "status",
        "created_at",
        "updated_at",
        "user_id",
    }
    assert body["title"] == "UI Display Test"
    assert body["description"] == "Immediate visibility"
    assert body["status"] is False
    assert isinstance(body["id"], str)
    assert isinstance(body["user_id"], str)
    assert isinstance(body["created_at"], str)
    assert isinstance(body["updated_at"], str)

    list_response = client.get(f"{prefix}/todo/")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed == [body]
