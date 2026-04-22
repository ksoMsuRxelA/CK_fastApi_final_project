"""Интеграционные тесты для эндпоинта /study-plan."""
from fastapi.testclient import TestClient


def _seed_demo_graph(
    client: TestClient, headers: dict[str, str]
) -> dict[str, int]:
    """Создать демо-граф из 6 курсов и вернуть словарь код -> id."""
    courses = [
        ("MATH101", "Calculus I", 5),
        ("CS101", "Intro Programming", 4),
        ("CS201", "Data Structures", 5),
        ("CS202", "Discrete Math", 4),
        ("CS301", "Algorithms", 5),
        ("ENG101", "English", 2),
    ]
    ids: dict[str, int] = {}
    for code, title, credits in courses:
        r = client.post(
            "/courses",
            json={"code": code, "title": title, "credits": credits},
            headers=headers,
        )
        ids[code] = r.json()["id"]

    edges = [
        ("CS201", "CS101"),
        ("CS202", "CS101"),
        ("CS202", "MATH101"),
        ("CS301", "CS201"),
        ("CS301", "CS202"),
    ]
    for course_code, prereq_code in edges:
        client.post(
            f"/courses/{ids[course_code]}/prerequisites",
            json={"prereq_id": ids[prereq_code]},
            headers=headers,
        )
    return ids


class TestStudyPlanEndpoint:

    def test_requires_auth(self, client: TestClient) -> None:
        r = client.post(
            "/study-plan",
            json={"target_course_id": 1, "max_credits_per_semester": 10},
        )
        assert r.status_code == 401

    def test_basic_plan(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        ids = _seed_demo_graph(client, user_headers)

        r = client.post(
            "/study-plan",
            json={
                "target_course_id": ids["CS301"],
                "max_credits_per_semester": 10,
            },
            headers=user_headers,
        )
        assert r.status_code == 200
        plan = r.json()
        assert plan["target_course_id"] == ids["CS301"]
        # Для CS301 нужны CS101, MATH101, CS201, CS202, сам CS301 → 5 курсов
        assert plan["total_courses"] == 5

        # Последний семестр должен содержать только CS301
        last_sem = plan["semesters"][-1]
        assert len(last_sem["courses"]) == 1
        assert last_sem["courses"][0]["course_code"] == "CS301"

    def test_orphan_courses_excluded(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        """ENG101 не нужен для CS301, не должен попасть в план."""
        ids = _seed_demo_graph(client, user_headers)
        r = client.post(
            "/study-plan",
            json={
                "target_course_id": ids["CS301"],
                "max_credits_per_semester": 10,
            },
            headers=user_headers,
        )
        all_codes = {
            c["course_code"]
            for s in r.json()["semesters"]
            for c in s["courses"]
        }
        assert "ENG101" not in all_codes

    def test_credit_limit_respected(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        ids = _seed_demo_graph(client, user_headers)
        limit = 8
        r = client.post(
            "/study-plan",
            json={
                "target_course_id": ids["CS301"],
                "max_credits_per_semester": limit,
            },
            headers=user_headers,
        )
        for sem in r.json()["semesters"]:
            assert sem["total_credits"] <= limit

    def test_completed_from_request_body(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        ids = _seed_demo_graph(client, user_headers)
        r = client.post(
            "/study-plan",
            json={
                "target_course_id": ids["CS301"],
                "max_credits_per_semester": 10,
                "completed_course_ids": [ids["CS101"], ids["MATH101"]],
            },
            headers=user_headers,
        )
        plan = r.json()
        all_codes = {
            c["course_code"]
            for s in plan["semesters"]
            for c in s["courses"]
        }
        assert "CS101" not in all_codes
        assert "MATH101" not in all_codes
        assert plan["total_courses"] == 3  # CS201, CS202, CS301

    def test_completed_from_enrollments(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        """Если completed_course_ids пустой, берутся из enrollments."""
        ids = _seed_demo_graph(client, user_headers)

        # Отметим CS101 как пройденный через enrollments
        client.post(
            "/users/me/enrollments",
            json={"course_id": ids["CS101"], "status": "completed"},
            headers=user_headers,
        )

        r = client.post(
            "/study-plan",
            json={
                "target_course_id": ids["CS301"],
                "max_credits_per_semester": 10,
            },
            headers=user_headers,
        )
        all_codes = {
            c["course_code"]
            for s in r.json()["semesters"]
            for c in s["courses"]
        }
        assert "CS101" not in all_codes

    def test_missing_target_returns_404(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        r = client.post(
            "/study-plan",
            json={
                "target_course_id": 9999,
                "max_credits_per_semester": 10,
            },
            headers=user_headers,
        )
        assert r.status_code == 404

    def test_credit_limit_too_small(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        ids = _seed_demo_graph(client, user_headers)
        # MATH101 стоит 5 кредитов, в лимит 4 не помещается
        r = client.post(
            "/study-plan",
            json={
                "target_course_id": ids["CS301"],
                "max_credits_per_semester": 4,
            },
            headers=user_headers,
        )
        assert r.status_code == 400

    def test_target_already_completed_empty_plan(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        ids = _seed_demo_graph(client, user_headers)
        r = client.post(
            "/study-plan",
            json={
                "target_course_id": ids["CS101"],
                "max_credits_per_semester": 10,
                "completed_course_ids": [ids["CS101"]],
            },
            headers=user_headers,
        )
        assert r.status_code == 200
        assert r.json()["total_courses"] == 0
