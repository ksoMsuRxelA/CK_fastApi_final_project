"""Тесты CRUD для курсов."""
from fastapi.testclient import TestClient


class TestListCourses:

    def test_empty_catalog(self, client: TestClient) -> None:
        r = client.get("/courses")
        assert r.status_code == 200
        assert r.json() == []

    def test_public_access_no_auth_required(self, client: TestClient) -> None:
        r = client.get("/courses")
        assert r.status_code == 200


class TestCreateCourse:

    def test_create_requires_auth(self, client: TestClient) -> None:
        r = client.post(
            "/courses",
            json={"code": "CS101", "title": "Intro", "credits": 4},
        )
        assert r.status_code == 401

    def test_create_success(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.post(
            "/courses",
            json={"code": "CS101", "title": "Intro", "credits": 4},
            headers=user_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["code"] == "CS101"
        assert body["credits"] == 4
        assert "id" in body

    def test_duplicate_code_rejected(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        client.post(
            "/courses",
            json={"code": "CS101", "title": "A", "credits": 4},
            headers=user_headers,
        )
        r = client.post(
            "/courses",
            json={"code": "CS101", "title": "B", "credits": 3},
            headers=user_headers,
        )
        assert r.status_code == 409

    def test_invalid_code_format(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.post(
            "/courses",
            json={"code": "cs101", "title": "X", "credits": 4},
            headers=user_headers,
        )
        assert r.status_code == 422

    def test_credits_out_of_range(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.post(
            "/courses",
            json={"code": "BAD1", "title": "X", "credits": 99},
            headers=user_headers,
        )
        assert r.status_code == 422


class TestUpdateCourse:

    def test_patch_partial(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.post(
            "/courses",
            json={"code": "CS101", "title": "Old", "credits": 4},
            headers=user_headers,
        )
        course_id = r.json()["id"]

        r = client.patch(
            f"/courses/{course_id}",
            json={"title": "New Title"},
            headers=user_headers,
        )
        assert r.status_code == 200
        assert r.json()["title"] == "New Title"
        assert r.json()["code"] == "CS101"

    def test_patch_missing_course(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.patch(
            "/courses/9999",
            json={"title": "X"},
            headers=user_headers,
        )
        assert r.status_code == 404


class TestDeleteCourse:

    def test_delete_success(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.post(
            "/courses",
            json={"code": "CS101", "title": "X", "credits": 4},
            headers=user_headers,
        )
        course_id = r.json()["id"]

        r = client.delete(f"/courses/{course_id}", headers=user_headers)
        assert r.status_code == 204

        r = client.get(f"/courses/{course_id}")
        assert r.status_code == 404

    def test_delete_missing_course(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.delete("/courses/9999", headers=user_headers)
        assert r.status_code == 404
