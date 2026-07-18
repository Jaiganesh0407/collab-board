def _auth_headers(client, email="ada@example.com"):
    client.post("/api/auth/register", json={"name": "Ada", "email": email, "password": "password123"})
    res = client.post("/api/auth/login", data={"username": email, "password": "password123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_workspace_and_board(client):
    headers = _auth_headers(client)
    res = client.post("/api/workspaces", json={"name": "Acme"}, headers=headers)
    assert res.status_code == 201
    ws_id = res.json()["id"]

    res = client.post(f"/api/boards/workspace/{ws_id}", json={"name": "Sprint 1"}, headers=headers)
    assert res.status_code == 201
    board_id = res.json()["id"]

    res = client.get(f"/api/boards/{board_id}/full", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # default columns should be created
    assert [c["name"] for c in data["columns"]] == ["To Do", "In Progress", "Done"]


def test_card_creation_and_move(client):
    headers = _auth_headers(client)
    ws_id = client.post("/api/workspaces", json={"name": "Acme"}, headers=headers).json()["id"]
    board_id = client.post(f"/api/boards/workspace/{ws_id}", json={"name": "Sprint 1"}, headers=headers).json()["id"]
    board = client.get(f"/api/boards/{board_id}/full", headers=headers).json()
    todo_col = board["columns"][0]["id"]
    done_col = board["columns"][2]["id"]

    res = client.post("/api/cards", json={"title": "Fix bug", "column_id": todo_col, "position": 0}, headers=headers)
    assert res.status_code == 201
    card = res.json()
    assert card["version"] == 1

    res = client.patch(f"/api/cards/{card['id']}/move",
                        json={"column_id": done_col, "position": 0, "version": 1}, headers=headers)
    assert res.status_code == 200
    assert res.json()["version"] == 2
    assert res.json()["column_id"] == done_col


def test_optimistic_lock_conflict(client):
    """Moving a card with a stale version should be rejected with 409."""
    headers = _auth_headers(client)
    ws_id = client.post("/api/workspaces", json={"name": "Acme"}, headers=headers).json()["id"]
    board_id = client.post(f"/api/boards/workspace/{ws_id}", json={"name": "Sprint 1"}, headers=headers).json()["id"]
    board = client.get(f"/api/boards/{board_id}/full", headers=headers).json()
    todo_col = board["columns"][0]["id"]
    progress_col = board["columns"][1]["id"]

    card = client.post("/api/cards", json={"title": "Fix bug", "column_id": todo_col, "position": 0}, headers=headers).json()

    # first move succeeds and bumps version to 2
    client.patch(f"/api/cards/{card['id']}/move",
                 json={"column_id": progress_col, "position": 0, "version": 1}, headers=headers)

    # second move using the stale version=1 should conflict
    res = client.patch(f"/api/cards/{card['id']}/move",
                        json={"column_id": progress_col, "position": 1, "version": 1}, headers=headers)
    assert res.status_code == 409
