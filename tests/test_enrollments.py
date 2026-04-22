"""Тесты для записей пользователей на курсы."""
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, login, register_user


def _create_course(client: TestClient, headers: dict[str, str], code: str) -> int:
    r = client.post(
        "/courses",
        json={"code": code, "title": code, "credits": 4},
        headers=headers,
    )
    return r.json()["id"]


class TestCreateEnrollment:

    def test_requires_auth(self, client: TestClient) -> None:
        r = client.post("/users/me/enrollments", json={"course_id": 1})
        assert r.status_code == 401

    def test_create_success(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        course_id = _create_course(client, user_headers, "CS101")
        r = client.post(
            "/users/me/enrollments",
            json={"course_id": course_id, "status": "completed", "semester": 1},
            headers=user_headers,
        )
        assert r.status_code == 201
        assert r.json()["status"] == "completed"

    def test_duplicate_enrollment_rejected(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        course_id = _create_course(client, user_headers, "CS101")
        client.post(
            "/users/me/enrollments",
            json={"course_id": course_id, "status": "planned"},
            headers=user_headers,
        )
        r = client.post(
            "/users/me/enrollments",
            json={"course_id": course_id, "status": "in_progress"},
            headers=user_headers,
        )
        assert r.status_code == 409

    def test_missing_course(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.post(
            "/users/me/enrollments",
            json={"course_id": 9999},
            headers=user_headers,
        )
        assert r.status_code == 404

    def test_invalid_status(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        course_id = _create_course(client, user_headers, "CS101")
        r = client.post(
            "/users/me/enrollments",
            json={"course_id": course_id, "status": "nonsense"},
            headers=user_headers,
        )
        assert r.status_code == 422


class TestUserIsolation:

    def test_cannot_access_other_users_enrollment(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        course_id = _create_course(client, user_headers, "CS101")
        r = client.post(
            "/users/me/enrollments",
            json={"course_id": course_id, "status": "completed"},
            headers=user_headers,
        )
        enrollment_id = r.json()["id"]

        # Второй пользователь
        register_user(client, email="other@example.com")
        other_token = login(client, email="other@example.com")
        other_headers = auth_headers(other_token)

        # Не должен видеть запись первого
        r = client.get("/users/me/enrollments", headers=other_headers)
        assert r.status_code == 200
        assert r.json() == []

        # Не должен её менять
        r = client.patch(
            f"/users/me/enrollments/{enrollment_id}",
            json={"status": "planned"},
            headers=other_headers,
        )
        assert r.status_code == 404

        # Не должен её удалять
        r = client.delete(
            f"/users/me/enrollments/{enrollment_id}", headers=other_headers
        )
        assert r.status_code == 404


class TestUpdateEnrollment:

    def test_patch_status(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        course_id = _create_course(client, user_headers, "CS101")
        r = client.post(
            "/users/me/enrollments",
            json={"course_id": course_id, "status": "planned"},
            headers=user_headers,
        )
        enrollment_id = r.json()["id"]

        r = client.patch(
            f"/users/me/enrollments/{enrollment_id}",
            json={"status": "completed"},
            headers=user_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "completed"


class TestCascadeDelete:

    def test_deleting_course_removes_enrollment(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        course_id = _create_course(client, user_headers, "CS101")
        r = client.post(
            "/users/me/enrollments",
            json={"course_id": course_id, "status": "planned"},
            headers=user_headers,
        )
        enrollment_id = r.json()["id"]

        client.delete(f"/courses/{course_id}", headers=user_headers)

        r = client.get("/users/me/enrollments", headers=user_headers)
        assert all(e["id"] != enrollment_id for e in r.json())
