"""Тесты аутентификации: регистрация, логин, /auth/me."""
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, login, register_user


class TestRegister:

    def test_register_success(self, client: TestClient) -> None:
        r = client.post(
            "/auth/register",
            json={
                "email": "new@example.com",
                "full_name": "New User",
                "password": "supersecret123",
            },
        )
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "new@example.com"
        assert body["full_name"] == "New User"
        assert "id" in body
        assert "password" not in body

    def test_register_duplicate_email(self, client: TestClient) -> None:
        register_user(client)
        r = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "full_name": "Duplicate",
                "password": "supersecret123",
            },
        )
        assert r.status_code == 409

    def test_register_invalid_email(self, client: TestClient) -> None:
        r = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "full_name": "X",
                "password": "supersecret123",
            },
        )
        assert r.status_code == 422

    def test_register_short_password(self, client: TestClient) -> None:
        r = client.post(
            "/auth/register",
            json={"email": "x@y.com", "full_name": "X", "password": "short"},
        )
        assert r.status_code == 422

    def test_register_password_over_72_bytes(self, client: TestClient) -> None:
        r = client.post(
            "/auth/register",
            json={"email": "x@y.com", "full_name": "X", "password": "a" * 73},
        )
        assert r.status_code == 422


class TestLogin:

    def test_login_success(self, client: TestClient) -> None:
        register_user(client)
        r = client.post(
            "/auth/login",
            data={"username": "user@example.com", "password": "supersecret123"},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert r.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient) -> None:
        register_user(client)
        r = client.post(
            "/auth/login",
            data={"username": "user@example.com", "password": "wrong"},
        )
        assert r.status_code == 401

    def test_login_unknown_user(self, client: TestClient) -> None:
        r = client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "whatever123"},
        )
        assert r.status_code == 401


class TestAuthMe:

    def test_me_without_token(self, client: TestClient) -> None:
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_with_invalid_token(self, client: TestClient) -> None:
        r = client.get("/auth/me", headers=auth_headers("garbage"))
        assert r.status_code == 401

    def test_me_returns_current_user(self, client: TestClient) -> None:
        register_user(client)
        token = login(client)
        r = client.get("/auth/me", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["email"] == "user@example.com"
