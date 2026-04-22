# Study Planner API

REST-сервис на FastAPI для планирования учебной траектории студента.

Пользователь выбирает целевой курс, указывает уже пройденные курсы и
ограничение по нагрузке — сервис строит оптимальный план прохождения
курсов по семестрам с учётом префеквизитов.

## Стек

- **Python 3.12**, FastAPI, SQLAlchemy 2.x (async), Alembic
- **PostgreSQL 16** (dev), SQLite (тесты)
- **JWT** через OAuth2 Password Flow
- **pytest** + httpx для автотестов
- **Docker Compose** для локального запуска

## Ключевые возможности

- Регистрация / логин / защищённые эндпоинты
- CRUD для курсов, префеквизитов, записей пользователя
- **Детектирование циклов в графе префеквизитов** (DFS) при добавлении ребра
- **Алгоритмический эндпоинт** `POST /study-plan` — построение плана
  через топологическую сортировку + HLF-эвристика + жадная упаковка
  по семестрам
- Автоподхват пройденных курсов из записей пользователя

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

После старта:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

При первом запуске контейнер приложения автоматически применит все
миграции Alembic.

## Миграции

```bash
docker compose exec app alembic upgrade head       # применить
docker compose exec app alembic downgrade -1      # откатить одну
docker compose exec app alembic revision \
    --autogenerate -m "message"                    # создать новую
```

## Тесты

Тесты запускаются через pytest и используют SQLite in-memory
(PostgreSQL для них не нужен):

```bash
# локально, без контейнера
pip install -r requirements.txt
JWT_SECRET=test python -m pytest tests/ -v

# или внутри контейнера
docker compose exec app python -m pytest tests/ -v
```

Должно быть 58 passed.

## Проверка качества кода

```bash
python -m pylint app > pylint.txt
cat pylint.txt
```

Текущая оценка — **10.00/10**.

## Структура проекта

```
app/
├── main.py                   # точка входа FastAPI
├── config.py                 # настройки из .env
├── database.py               # SQLAlchemy engine, async-сессии
├── dependencies.py           # FastAPI-зависимости (get_current_user)
├── models/                   # ORM-модели: User, Course, Prerequisite, Enrollment
├── schemas/                  # Pydantic-схемы запросов/ответов
├── routes/                   # HTTP-эндпоинты по доменам
├── services/                 # бизнес-логика поверх БД
├── algorithms/
│   └── study_plan.py         # чистый алгоритм: топсорт + HLF + упаковка
└── auth/                     # bcrypt, JWT
tests/                        # 58 автотестов
migrations/                   # Alembic
```

## Эндпоинты

| Метод | Путь | Auth | Описание |
|-------|------|------|----------|
| POST | `/auth/register` | — | Регистрация |
| POST | `/auth/login` | — | Логин, получение JWT |
| GET | `/auth/me` | ✓ | Текущий пользователь |
| GET | `/courses` | — | Список курсов |
| GET | `/courses/{id}` | — | Детали курса |
| POST | `/courses` | ✓ | Создать курс |
| PATCH | `/courses/{id}` | ✓ | Обновить курс |
| DELETE | `/courses/{id}` | ✓ | Удалить курс |
| GET | `/courses/{id}/prerequisites` | — | Префеквизиты курса |
| POST | `/courses/{id}/prerequisites` | ✓ | Добавить префеквизит |
| DELETE | `/courses/{id}/prerequisites/{prereq_id}` | ✓ | Удалить префеквизит |
| GET | `/users/me/enrollments` | ✓ | Мои записи |
| POST | `/users/me/enrollments` | ✓ | Записаться на курс |
| PATCH | `/users/me/enrollments/{id}` | ✓ | Обновить запись |
| DELETE | `/users/me/enrollments/{id}` | ✓ | Удалить запись |
| POST | `/study-plan` | ✓ | Построить учебный план |

## Про алгоритм

Задача построения плана в общем виде **NP-hard**: это обобщение
bin-packing с precedence-ограничениями. Используется жадная эвристика
HLF (Highest Level First):

1. **Сбор подграфа** — DFS вверх от целевого курса по рёбрам
   префеквизитов, пропуская уже пройденные. O(V+E)
2. **Вычисление весов** — для каждого курса считается число
   транзитивных потомков (сколько курсов "разблокирует"). O(V·(V+E))
3. **Упаковка по семестрам** — в каждом семестре кандидаты (курсы с
   уже пройденными префеквизитами) сортируются по убыванию веса и
   жадно упаковываются в лимит `max_credits_per_semester`.

Решение не гарантирует минимум семестров в худшем случае (это невозможно
за полиномиальное время без P=NP), но на реалистичных учебных графах
даёт близкие к оптимуму результаты.

## Автор

Ruslan Moskvitin
