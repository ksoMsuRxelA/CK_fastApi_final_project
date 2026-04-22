"""Юнит-тесты чистой функции build_study_plan без HTTP/БД."""
import pytest

from app.algorithms.study_plan import (
    CourseNode,
    CoursesMissingError,
    CreditLimitExceededError,
    build_study_plan,
)


def _linear_chain() -> tuple[list[CourseNode], list[tuple[int, int]]]:
    """A <- B <- C <- D (D зависит от C зависит от B зависит от A)."""
    courses = [
        CourseNode(1, 3),
        CourseNode(2, 3),
        CourseNode(3, 3),
        CourseNode(4, 3),
    ]
    edges = [(2, 1), (3, 2), (4, 3)]
    return courses, edges


class TestSimpleCases:

    def test_single_course_no_prereqs(self) -> None:
        courses = [CourseNode(1, 4)]
        plan = build_study_plan(
            all_courses=courses,
            prerequisites=[],
            target_id=1,
            completed_ids=set(),
            max_credits_per_semester=10,
        )
        assert plan.total_courses == 1
        assert len(plan.semesters) == 1
        assert plan.semesters[0].courses[0].course_id == 1

    def test_linear_chain_generates_sequential_semesters(self) -> None:
        """В цепочке A->B->C->D каждый курс должен быть в своём семестре
        (при лимите, позволяющем только один курс за семестр)."""
        courses, edges = _linear_chain()
        plan = build_study_plan(
            all_courses=courses,
            prerequisites=edges,
            target_id=4,
            completed_ids=set(),
            max_credits_per_semester=3,
        )
        assert len(plan.semesters) == 4
        for sem_num, expected_id in enumerate([1, 2, 3, 4], start=1):
            sem = plan.semesters[sem_num - 1]
            assert sem.courses[0].course_id == expected_id

    def test_target_already_completed_returns_empty(self) -> None:
        courses = [CourseNode(1, 4)]
        plan = build_study_plan(
            all_courses=courses,
            prerequisites=[],
            target_id=1,
            completed_ids={1},
            max_credits_per_semester=10,
        )
        assert plan.semesters == []
        assert plan.total_courses == 0


class TestPriorityAndPacking:

    def test_credits_cap_enforced(self) -> None:
        """Три курса по 4 кредита с общими префеквизитами не влезут в лимит 10
        одним семестром — получим минимум 2 семестра или один с 2 курсами."""
        courses = [CourseNode(1, 4), CourseNode(2, 4), CourseNode(3, 4)]
        plan = build_study_plan(
            all_courses=courses,
            prerequisites=[(3, 1), (3, 2)],
            target_id=3,
            completed_ids=set(),
            max_credits_per_semester=10,
        )
        for sem in plan.semesters:
            assert sem.total_credits <= 10

    def test_orphan_courses_not_included(self) -> None:
        """Курс, не являющийся префеквизитом цели, не должен попасть в план."""
        courses = [
            CourseNode(1, 4),   # target
            CourseNode(2, 4),   # orphan
        ]
        plan = build_study_plan(
            all_courses=courses,
            prerequisites=[],
            target_id=1,
            completed_ids=set(),
            max_credits_per_semester=10,
        )
        ids_in_plan = {
            pc.course_id for s in plan.semesters for pc in s.courses
        }
        assert 2 not in ids_in_plan
        assert ids_in_plan == {1}

    def test_hlf_priority_picks_bottleneck_first(self) -> None:
        """Если два курса-кандидата, но один разблокирует больше других,
        он должен идти раньше в семестре (первым в списке)."""
        # Граф: A и B — оба без префеквизитов. C требует A. D требует C.
        # E требует B. Цель — D и E через общий корневой семестр.
        # Создадим ситуацию: target = F. F требует D, E.
        # A -> C -> D (разблокирует 2 курса)
        # B -> E (разблокирует 1 курс)
        # В первом семестре оба A и B — A должен быть приоритетнее B (вес 3 vs 2).
        courses = [CourseNode(i, 3) for i in range(1, 7)]
        # 1=A, 2=B, 3=C, 4=D, 5=E, 6=F(target)
        edges = [(3, 1), (4, 3), (5, 2), (6, 4), (6, 5)]
        plan = build_study_plan(
            all_courses=courses,
            prerequisites=edges,
            target_id=6,
            completed_ids=set(),
            max_credits_per_semester=3,  # вмещаем по одному курсу
        )
        # Первый семестр: должен взять A (id=1), у него больший вес
        assert plan.semesters[0].courses[0].course_id == 1


class TestErrorCases:

    def test_missing_target_raises(self) -> None:
        with pytest.raises(CoursesMissingError):
            build_study_plan(
                all_courses=[CourseNode(1, 4)],
                prerequisites=[],
                target_id=999,
                completed_ids=set(),
                max_credits_per_semester=10,
            )

    def test_course_over_limit_raises(self) -> None:
        courses = [CourseNode(1, 10)]
        with pytest.raises(CreditLimitExceededError):
            build_study_plan(
                all_courses=courses,
                prerequisites=[],
                target_id=1,
                completed_ids=set(),
                max_credits_per_semester=5,
            )


class TestCompletedPrerequisites:

    def test_completed_skipped_transitively(self) -> None:
        """В цепочке A->B->C->D если B пройден, план включает только C и D."""
        courses, edges = _linear_chain()
        plan = build_study_plan(
            all_courses=courses,
            prerequisites=edges,
            target_id=4,
            completed_ids={1, 2},
            max_credits_per_semester=3,
        )
        ids_in_plan = {
            pc.course_id for s in plan.semesters for pc in s.courses
        }
        assert ids_in_plan == {3, 4}
