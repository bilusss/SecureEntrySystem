from fastapi.testclient import TestClient
from app.main import app
from app.schemas import UserCreate
from app.users import get_user_manager
import asyncio

def test_register_and_login(client: TestClient):
    response = client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "password123"
    })
    assert response.status_code == 201

    response = client.post("/auth/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    assert response.status_code == 200

    cookies = client.cookies
    assert "session" in cookies
