def test_register_and_login(client):
    res = client.post("/api/auth/register", json={
        "name": "Ada Lovelace", "email": "ada@example.com", "password": "password123",
    })
    assert res.status_code == 201
    assert res.json()["email"] == "ada@example.com"

    res = client.post("/api/auth/login", data={
        "username": "ada@example.com", "password": "password123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "name": "Ada", "email": "ada@example.com", "password": "password123",
    })
    res = client.post("/api/auth/login", data={
        "username": "ada@example.com", "password": "wrongpassword",
    })
    assert res.status_code == 401


def test_duplicate_email_rejected(client):
    payload = {"name": "Ada", "email": "ada@example.com", "password": "password123"}
    client.post("/api/auth/register", json=payload)
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400


def test_me_requires_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
