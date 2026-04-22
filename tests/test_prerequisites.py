"""Тесты для префеквизитов и детектирования циклов."""
from fastapi.testclient import TestClient


def _create_course(
    client: TestClient,
    headers: dict[str, str],
    code: str,
    credits: int = 4,
) -> int:
    """Хелпер: создать курс и вернуть его id."""
    # Pydantic требует min_length=2, поэтому короткие коды дополняем.
    full_code = code if len(code) >= 2 else f"C{code}"
    r = client.post(
        "/courses",
        json={"code": full_code, "title": code, "credits": credits},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


class TestAddPrerequisite:

    def test_add_simple_edge(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        a = _create_course(client, user_headers, "A")
        b = _create_course(client, user_headers, "B")

        r = client.post(
            f"/courses/{b}/prerequisites",
            json={"prereq_id": a},
            headers=user_headers,
        )
        assert r.status_code == 201

    def test_requires_auth(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        a = _create_course(client, user_headers, "A")
        b = _create_course(client, user_headers, "B")

        r = client.post(
            f"/courses/{b}/prerequisites", json={"prereq_id": a}
        )
        assert r.status_code == 401

    def test_duplicate_edge_rejected(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        a = _create_course(client, user_headers, "A")
        b = _create_course(client, user_headers, "B")

        client.post(
            f"/courses/{b}/prerequisites",
            json={"prereq_id": a},
            headers=user_headers,
        )
        r = client.post(
            f"/courses/{b}/prerequisites",
            json={"prereq_id": a},
            headers=user_headers,
        )
        assert r.status_code == 409

    def test_missing_course_returns_404(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        a = _create_course(client, user_headers, "A")
        r = client.post(
            "/courses/9999/prerequisites",
            json={"prereq_id": a},
            headers=user_headers,
        )
        assert r.status_code == 404


class TestCycleDetection:

    def test_self_loop_rejected(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        a = _create_course(client, user_headers, "A")
        r = client.post(
            f"/courses/{a}/prerequisites",
            json={"prereq_id": a},
            headers=user_headers,
        )
        assert r.status_code == 409

    def test_direct_cycle(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        """A -> B уже есть, попытка добавить B -> A создаёт цикл."""
        a = _create_course(client, user_headers, "A")
        b = _create_course(client, user_headers, "B")

        client.post(
            f"/courses/{b}/prerequisites",
            json={"prereq_id": a},
            headers=user_headers,
        )
        r = client.post(
            f"/courses/{a}/prerequisites",
            json={"prereq_id": b},
            headers=user_headers,
        )
        assert r.status_code == 409
        assert "cycle" in r.json()["detail"].lower()

    def test_transitive_cycle(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        """C -> B -> A уже есть, попытка добавить A -> C создаёт цикл длины 3."""
        a = _create_course(client, user_headers, "A")
        b = _create_course(client, user_headers, "B")
        c = _create_course(client, user_headers, "C")

        client.post(
            f"/courses/{b}/prerequisites",
            json={"prereq_id": a},
            headers=user_headers,
        )
        client.post(
            f"/courses/{c}/prerequisites",
            json={"prereq_id": b},
            headers=user_headers,
        )
        r = client.post(
            f"/courses/{a}/prerequisites",
            json={"prereq_id": c},
            headers=user_headers,
        )
        assert r.status_code == 409

    def test_diamond_graph_is_not_cycle(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        """B -> A, C -> A, D -> B, D -> C: это не цикл, должно сработать."""
        a = _create_course(client, user_headers, "A")
        b = _create_course(client, user_headers, "B")
        c = _create_course(client, user_headers, "C")
        d = _create_course(client, user_headers, "D")

        for course, prereq in [(b, a), (c, a), (d, b), (d, c)]:
            r = client.post(
                f"/courses/{course}/prerequisites",
                json={"prereq_id": prereq},
                headers=user_headers,
            )
            assert r.status_code == 201


class TestRemovePrerequisite:

    def test_delete_existing(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        a = _create_course(client, user_headers, "A")
        b = _create_course(client, user_headers, "B")
        client.post(
            f"/courses/{b}/prerequisites",
            json={"prereq_id": a},
            headers=user_headers,
        )
        r = client.delete(
            f"/courses/{b}/prerequisites/{a}", headers=user_headers
        )
        assert r.status_code == 204

    def test_delete_missing_returns_404(
        self, client: TestClient, user_headers: dict[str, str]
    ) -> None:
        a = _create_course(client, user_headers, "A")
        b = _create_course(client, user_headers, "B")
        r = client.delete(
            f"/courses/{b}/prerequisites/{a}", headers=user_headers
        )
        assert r.status_code == 404
