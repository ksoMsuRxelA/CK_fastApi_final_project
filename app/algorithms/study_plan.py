"""Алгоритм построения учебного плана.

Решает задачу: дан DAG курсов с весами (credits) и рёбрами префеквизитов,
целевой курс и уже пройденное множество. Построить план по семестрам так,
чтобы сумма credits в каждом семестре не превышала заданного лимита,
а префеквизиты проходились в предыдущих семестрах.

Задача в общем случае NP-hard (обобщение bin-packing с precedence-ограничениями).
Используется жадная эвристика HLF (Highest Level First): приоритет курсам,
от которых транзитивно зависит больше других.

Сложность: O(V + E) на сборку подграфа и вычисление весов,
O(V^2) в худшем случае на саму упаковку — доминирует пересортировка.
"""
from dataclasses import dataclass


class CoursesMissingError(Exception):
    """В каталоге нет одного или нескольких запрошенных курсов."""

    def __init__(self, missing_ids: set[int]):
        super().__init__(f"Courses not found: {sorted(missing_ids)}")
        self.missing_ids = missing_ids


class CreditLimitExceededError(Exception):
    """Есть курс, который не помещается даже в пустой семестр."""

    def __init__(self, course_id: int, credits: int, limit: int):
        super().__init__(
            f"Course {course_id} has {credits} credits, "
            f"which exceeds per-semester limit of {limit}"
        )
        self.course_id = course_id
        self.credits = credits
        self.limit = limit


@dataclass(frozen=True)
class CourseNode:
    """Узел графа: минимум данных, нужных алгоритму."""

    id: int
    credits: int


@dataclass
class PlannedCourse:
    """Курс, попавший в план."""

    course_id: int
    credits: int


@dataclass
class Semester:
    """Один семестр плана."""

    number: int
    courses: list[PlannedCourse]
    total_credits: int


@dataclass
class StudyPlan:
    """Итоговый план: список семестров + агрегаты."""

    semesters: list[Semester]
    total_credits: int
    total_courses: int


def _collect_needed(
    target_id: int,
    prereqs_of: dict[int, list[int]],
    completed: set[int],
) -> set[int]:
    """BFS/DFS вверх по рёбрам от target_id, пропуская уже пройденные."""
    needed: set[int] = set()
    stack = [target_id]
    while stack:
        node = stack.pop()
        if node in completed or node in needed:
            continue
        needed.add(node)
        for prereq_id in prereqs_of.get(node, ()):
            if prereq_id not in completed and prereq_id not in needed:
                stack.append(prereq_id)
    return needed


def _compute_weights(
    nodes: set[int],
    prereqs_of: dict[int, list[int]],
) -> dict[int, int]:
    """Для каждого узла — число транзитивных потомков в индуцированном подграфе.

    "Потомок" в нашем графе — это курс, которому ЭТОТ курс является префеквизитом
    (прямо или транзитивно). Чем больше потомков — тем раньше стоит пройти курс,
    чтобы "разблокировать" их.
    """
    # Обратный граф: для каждого курса — список курсов, которым он нужен.
    dependents_of: dict[int, set[int]] = {n: set() for n in nodes}
    for course_id, prereqs in prereqs_of.items():
        if course_id not in nodes:
            continue
        for prereq_id in prereqs:
            if prereq_id in nodes:
                dependents_of[prereq_id].add(course_id)

    # Транзитивное замыкание через DFS от каждого узла по обратным рёбрам.
    weights: dict[int, int] = {}
    for node in nodes:
        visited: set[int] = set()
        stack = list(dependents_of[node])
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            stack.extend(dependents_of[cur] - visited)
        weights[node] = len(visited)
    return weights


def build_study_plan(
    *,
    all_courses: list[CourseNode],
    prerequisites: list[tuple[int, int]],
    target_id: int,
    completed_ids: set[int],
    max_credits_per_semester: int,
) -> StudyPlan:
    """Построить план прохождения курсов до целевого.

    Args:
        all_courses: все курсы в каталоге.
        prerequisites: рёбра (course_id, prereq_id) — "course_id требует prereq_id".
        target_id: целевой курс.
        completed_ids: id уже пройденных курсов.
        max_credits_per_semester: ограничение нагрузки на семестр.

    Raises:
        CoursesMissingError: если target_id нет в каталоге.
        CreditLimitExceededError: если курс не помещается в семестр даже в одиночку.
    """
    catalog = {c.id: c for c in all_courses}

    # Проверка существования целевого курса
    if target_id not in catalog:
        raise CoursesMissingError({target_id})

    # Индекс префеквизитов: course_id -> [prereq_id, ...]
    prereqs_of: dict[int, list[int]] = {}
    for course_id, prereq_id in prerequisites:
        prereqs_of.setdefault(course_id, []).append(prereq_id)

    # 1. Собрать нужное подмножество курсов
    needed = _collect_needed(target_id, prereqs_of, completed_ids)

    # Если целевой курс уже пройден — вернуть пустой план
    if not needed:
        return StudyPlan(semesters=[], total_credits=0, total_courses=0)

    # Проверим, что все нужные курсы есть в каталоге
    missing = needed - catalog.keys()
    if missing:
        raise CoursesMissingError(missing)

    # Проверим, что все курсы помещаются в лимит
    for course_id in needed:
        course_credits = catalog[course_id].credits
        if course_credits > max_credits_per_semester:
            raise CreditLimitExceededError(
                course_id, course_credits, max_credits_per_semester
            )

    # 2. Вычислить веса (HLF-приоритет)
    weights = _compute_weights(needed, prereqs_of)

    # 3. Итеративно набирать семестры.
    # В каждом семестре: кандидаты = курсы, чьи префеквизиты все в done.
    # Сортируем по убыванию веса, жадно упаковываем в лимит.
    remaining = set(needed)
    done = set(completed_ids)
    semesters: list[Semester] = []
    semester_num = 0

    while remaining:
        semester_num += 1
        # Кандидаты: все префеквизиты уже пройдены (или не нужны).
        candidates = sorted(
            (
                c for c in remaining
                if all(
                    p in done or p not in needed
                    for p in prereqs_of.get(c, ())
                )
            ),
            key=lambda c: (-weights[c], catalog[c].credits, c),
        )

        # Жадная упаковка
        picked: list[PlannedCourse] = []
        used_credits = 0
        for course_id in candidates:
            course_credits = catalog[course_id].credits
            if used_credits + course_credits <= max_credits_per_semester:
                picked.append(
                    PlannedCourse(course_id=course_id, credits=course_credits)
                )
                used_credits += course_credits

        if not picked:
            # Защита от бесконечного цикла — не должно случаться после проверок выше,
            # но на всякий случай.
            raise RuntimeError(
                f"Cannot progress at semester {semester_num}: "
                f"remaining={sorted(remaining)}"
            )

        semesters.append(
            Semester(
                number=semester_num,
                courses=picked,
                total_credits=used_credits,
            )
        )
        for pc in picked:
            done.add(pc.course_id)
            remaining.discard(pc.course_id)

    return StudyPlan(
        semesters=semesters,
        total_credits=sum(s.total_credits for s in semesters),
        total_courses=sum(len(s.courses) for s in semesters),
    )
