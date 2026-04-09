---
description: 
alwaysApply: true
---

# CLAUDE.md — Справочник по проекту Flokify (B2B Marketplace)

> Этот файл читается в начале каждого нового чата. Содержит всё необходимое для работы с проектом.

---

## 1. ОБЗОР ПРОЕКТА
**Технологический стек:**
- Python 3.12.7, FastAPI 0.116.1
- PostgreSQL 16.2 (asyncpg 0.30.0) — без ORM, raw SQL через Query Executor
- Redis 7 (redis 6.4.0) — кэш, очереди задач
- Granian 2.6.1 — ASGI-сервер (production)
- Pydantic 2.11.7, orjson 3.11.1, Loguru 0.7.3
- Docker / docker-compose, Nginx

---

## 2. БЫСТРЫЙ СТАРТ

### Установка зависимостей
```bash
# Используется uv (не pip, не poetry)
pip install uv
uv sync
```

### Dev-запуск (docker-compose)
```bash
cp .env.example .env
# Заполнить .env секретами
docker-compose -f docker-compose.dev.yml up --build
```

### Production-запуск
```bash
docker-compose up --build -d
```

### Запуск без Docker (локально)
```bash
# Применить миграции
yoyo apply --batch --database "postgresql://" ./migrations

# Запустить сервер
granian --interface asgi --factory --host 0.0.0.0 --port 8001 --workers 1 src.main:create_app

# Или через uvicorn для разработки:
uvicorn src.main:create_app --factory --reload --port 8001
```

### Email worker (отдельный процесс)
```bash
python -m src.workers.email_worker
```

### Линтер
```bash
# Ruff — и линтер, и форматтер
ruff check .
ruff format .
```

### Тесты
Тесты отсутствуют (папка `tests/` содержит только `__init__.py`).

### Переменные окружения
Файл-пример: `.env.example` в корне репозитория.

**Обязательные:**
```env
POSTGRES_HOST, POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_PORT
APP_SECRET_KEY
SSMS_EMAIL, SSMS_PASSWORD, SSMS_WEBHOOK_SECRET
```

**Опциональные (defaults в config.yaml):**
```env
APP_PORT=8001
LOG_LEVEL=INFO
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Архитектурный паттерн

**Clean Architecture / Layered Architecture:**

```
HTTP Request
    ↓
Router (src/api/v1/routes/)       — валидация входа (Pydantic schemas), rate limiting
    ↓
Dependencies (api/dependencies.py) — получение сервисов из Container, аутентификация
    ↓
Service (src/services/)           — бизнес-логика, оркестрация, работа с доменными объектами
    ↓
Repository Interface (src/interfaces/repositories/) — абстракция над данными
    ↓
Repository Implementation (src/infrastructure/postgres/repository/) — SQL-запросы
    ↓
QueryExecutor (infrastructure/postgres/query_executor.py) — asyncpg pool
    ↓
PostgreSQL
```

### Dependency Injection Container

Контейнер живёт в `app.state.container`. Три уровня с ленивой инициализацией:
- `InfrastructureContainer` → соединения (DB, Redis, S3, SSMS)
- `RepositoryContainer` → репозитории (зависят от infra)
- `ServiceContainer` → сервисы (зависят от repos + infra)

Доступ в роутерах через `Depends(get_XXX_service)` из `api/dependencies.py`.

### Конфигурация

Трёхуровневый приоритет (высший → низший):
1. Переменные окружения (env vars)
2. `.env` файл (секреты)
3. `config.yaml` (несекретные дефолты)

Классы: `PostgresConfig`, `AppConfig`, `RedisConfig`, `SsmsConfig`, — все в `src/core/config.py`.

---

## 4. ОТВЕТСТВЕННОСТИ СЛОЁВ

Каждый слой архитектуры имеет **строго ограниченную зону ответственности**. Нарушение этих границ — архитектурный дефект, а не просто "стиль".

Правило простое: **каждый слой знает ровно столько, сколько ему нужно, и не байт больше.**

```
HTTP Request
    ↓
Router          — принял, распаковал, передал → вернул схему
    ↓
Service         — знает ЧТО и В КАКОМ ПОРЯДКЕ, не знает КАК технически
    ↓
Repository      — строит SQL-запросы, маппит строки → не знает о драйвере
    ↓
QueryExecutor   — единственный, кто знает об asyncpg и пуле соединений
    ↓
PostgreSQL
```

---

### Router (эндпоинт) — тупой транспортный слой

Роутер — это **тонкая транспортная прослойка** между HTTP и сервисом. Его задача: получить валидированные данные от Pydantic, передать примитивы в сервис, упаковать результат в схему ответа. Всё. Никакой логики — ни бизнесовой, ни условной.

Роутер не знает **почему** делается то или иное действие. Он знает только **что вызвать** и **что вернуть**.

**Роутер делает:**
- Принимает `request: Request` только для rate limiting или получения base URL
- Получает текущего пользователя через `Depends(get_verified_user)`
- Получает сервис через `Depends(get_xxx_service)`
- Распаковывает поля из Pydantic-схемы и передаёт их в сервис как примитивы
- Возвращает `XxxSchema.model_validate(result)`

**Роутер никогда не делает:**
- `if user.role == "admin":` — это бизнес-логика, она в сервисе
- `if not result:` с последующими действиями — это условие, оно в сервисе
- Обращение к репозиториям напрямую
- Что-либо с SQL, Redis, S3
- `await request.json()` вручную — для этого есть Pydantic-схема

```python
# ✅ Правильно — роутер тупой, передаёт примитивы, возвращает схему
@router.post("", response_model=JobSchema, status_code=status.HTTP_201_CREATED)
async def create_job(
        data: JobCreateRequest,
        current_user: Annotated[User, Depends(get_verified_user)],
        job_service: Annotated[JobService, Depends(get_job_service)],
):
    job = await job_service.create_job(
        owner_id=current_user.id,
        title=data.title,
        description=data.description,
    )
    return JobSchema.model_validate(job)

# ❌ Неправильно — в роутере появилась логика
@router.post("")
async def create_job(data: JobCreateRequest, current_user: User = Depends(get_verified_user)):
    if not current_user.is_verified:          # ← это бизнес-правило, не место роутеру
        raise HTTPException(status_code=403)
    if len(data.title) < 5:                   # ← валидация поля — задача Pydantic/сервиса
        raise HTTPException(status_code=422)
    job = await job_repo.create(data.dict())  # ← роутер не должен знать о репозитории
    return job
```

---

### Service — единственное место бизнес-логики

Сервис знает **что нужно сделать** и **в каком порядке**. Он оркестрирует сущности, репозитории и клиенты для достижения одной бизнес-цели. При этом сервис работает **исключительно с интерфейсами** — он не знает, что за `IUserRepository` стоит Postgres, а за `IRedisClient` — Redis.

Сервис — это последовательность шагов: получить данные → проверить инварианты → изменить состояние → сохранить → вернуть результат.

**Сервис делает:**
- Принимает в конструктор интерфейсы: `IUserRepository`, `IStorageClient`, `IRedisClient` и т.д.
- Содержит всю бизнес-логику: проверки, условия, ограничения
- Вызывает методы доменных сущностей (`user.record_failed_attempt()`, `job.assert_owner(user_id)`)
- Бросает доменные исключения: `NotFoundError`, `ForbiddenError`, `ConflictError`
- Оркестрирует несколько репозиториев/клиентов для достижения одной цели

**Сервис никогда не делает:**
- Не импортирует `asyncpg`, `redis.asyncio`, `aioboto3`, `httpx` — никаких конкретных драйверов
- Не строит SQL-запросы, не знает о таблицах БД или ключах Redis
- Не знает о HTTP-специфике: статус-кодах, заголовках, cookies
- Не принимает `Request` из FastAPI

```python
# ✅ Правильно — сервис оперирует интерфейсами и бизнес-логикой
class AuthService:
    def __init__(
        self,
        user_repo: IUserRepository,          # интерфейс, не PostgresUserRepository
        token_repo: IRefreshTokenRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ):
        self._user_repo = user_repo

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        user = await self._user_repo.get_by_email(email)
        if not user or not user.hashed_password:
            raise AuthenticationError("Неверные учетные данные")   # бизнес-инвариант
        if not self._password_service.verify_password(user.hashed_password, password):
            raise AuthenticationError("Неверные учетные данные")
        if not user.email_verified:
            raise EmailNotVerifiedError("Подтвердите email перед входом")
        access_token = self._token_service.create_access_token(user.id)
        refresh_token, expires_at = self._token_service.create_refresh_token()
        await self._token_repo.create(user_id=user.id, token=refresh_token, expires_at=expires_at)
        return user, access_token, refresh_token

# ❌ Неправильно — сервис знает о конкретном драйвере
class AuthService:
    def __init__(self, pool: asyncpg.Pool):   # ← прямая зависимость от asyncpg
        self._pool = pool

    async def login(self, email: str, password: str):
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)  # ← SQL в сервисе!
```

---

### Repository — строитель запросов и маппер строк

Репозиторий знает только одно: **как получить или сохранить данные в конкретном хранилище**. Он строит параметризованный SQL-запрос, передаёт его в `QueryExecutor` и маппит сырые строки в доменные сущности. Никакой логики — только SQL и маппинг.

Репозиторий не знает **зачем** запрашиваются данные. Он просто строит запрос и отдаёт результат.

**Репозиторий делает:**
- Строит параметризованные SQL-запросы с `$1, $2, ...`
- Вызывает `self._query_executor.fetch_row(query, *params)` / `fetch` / `execute`
- Маппит строку результата в доменную сущность через `_row_to_entity(row)`
- Динамически собирает WHERE-условия под фильтры (но не решает, какие фильтры применить)

**Репозиторий никогда не делает:**
- Не проверяет бизнес-правила: `if user.is_blocked(): raise ...` — это не его дело
- Не знает о других репозиториях
- Не обращается к Redis, S3, внешним API — только к своему хранилищу
- Не использует f-строки с пользовательскими данными в SQL (SQL-инъекция!)
- Не импортирует `asyncpg` напрямую — только через `IQueryExecutor`

```python
# ✅ Правильно — репозиторий строит запрос и маппит, больше ничего
class PostgresUserRepository(IUserRepository):
    __slots__ = ("_query_executor",)

    async def get_by_email(self, email: str) -> User | None:
        query = f"SELECT {_SELECT_FIELDS} FROM users WHERE email = $1"
        row = await self._query_executor.fetch_row(query, email)
        return self._row_to_user(row) if row else None

    @staticmethod
    def _row_to_user(row) -> User:
        return User(id=str(row["id"]), email=row["email"], ...)  # только маппинг

# ❌ Неправильно — репозиторий принимает бизнес-решения
async def get_by_email(self, email: str) -> User | None:
    row = await self._query_executor.fetch_row(query, email)
    user = self._row_to_user(row)
    if not user.email_verified:        # ← это бизнес-правило, не задача репозитория
        raise EmailNotVerifiedError()
    return user
```

---

### QueryExecutor — единственный знающий о драйвере

`QueryExecutor` — тонкая обёртка над `asyncpg`. Принимает готовый SQL и параметры, выполняет через пул соединений, возвращает сырые строки. Это единственный класс в проекте, который импортирует `asyncpg`.

Репозиторий не знает об `asyncpg.Pool`, о транзакциях, о курсорах — он работает только через методы `QueryExecutor`.

**Зона ответственности:** управление пулом соединений, выполнение готовых запросов, обработка низкоуровневых ошибок драйвера.

```
Репозиторий → передаёт SQL + параметры → QueryExecutor → asyncpg → PostgreSQL
```

---

### Domain Entity — носитель данных и бизнес-правил

Доменная сущность — это `@dataclass` с полями и методами, которые описывают бизнес-поведение **только одного объекта**. Сущность полностью изолирована: она не ходит в БД, не пишет в Redis, не делает HTTP-запросы. Она живёт только в памяти и знает только о себе.

Если правило касается только одной сущности — оно живёт внутри неё, а не в сервисе.

**Сущность делает:**
- Хранит поля с типами
- Содержит методы, которые зависят **только от собственных полей**
- Изменяет своё состояние (`confirm_verified()`, `record_failed_attempt()`)
- Бросает доменные исключения при нарушении собственных инвариантов (`assert_owner()`)

**Сущность никогда не делает:**
- Не импортирует ничего из `infrastructure`, `services`, `api`
- Не принимает репозитории, клиентов или сессии в аргументы методов
- Не делает `async` вызовов — никаких обращений во внешний мир

```python
# ✅ Правильно — сущность изолирована, знает только о себе
@dataclass(slots=True, kw_only=True)
class User:
    email_verified: bool = False
    verification_attempts: int = 0
    blocked_until: datetime | None = None

    def is_blocked(self) -> bool:
        return self.blocked_until is not None and self.blocked_until > utcnow()

    def record_failed_attempt(self, max_attempts: int = 5, block_minutes: int = 30) -> None:
        self.verification_attempts += 1
        if self.verification_attempts >= max_attempts:
            self.blocked_until = utcnow() + timedelta(minutes=block_minutes)
            self.verification_attempts = 0

    def confirm_verified(self) -> None:
        self.email_verified = True
        self.verification_attempts = 0
        self.blocked_until = None

# ❌ Неправильно — сущность знает о внешнем мире
@dataclass
class User:
    async def save(self, db_pool):              # ← сущность не сохраняет себя сама
        await db_pool.execute("UPDATE users ...", self.id)

    async def send_verification(self, smtp):    # ← сущность не отправляет письма
        await smtp.send(self.email, ...)
```

---

### Worker — тонкий планировщик вызовов сервиса

Воркер — это инфраструктурный компонент: polling-петля + graceful shutdown. Он знает только то, что есть **сервис**, и периодически его вызывает. Вся реальная работа (что делать с задачей, как её обработать) — делегируется сервису целиком.

Воркер не должен знать о структуре задачи, о типах событий, о том что конкретно происходит при обработке. Это всё — зона сервиса.

**Воркер делает:**
- Инициализирует инфраструктуру (Redis, конфиг) для передачи в сервис
- Реализует polling-петлю с паузами
- Обрабатывает graceful shutdown через signal handlers
- Вызывает `service.process(task)` и не смотрит внутрь

**Воркер никогда не делает:**
- Не содержит логику обработки конкретной задачи — это в сервисе
- Не смотрит внутрь задачи: `task["type"]`, `task["email"]` — сервис скрывает эти детали
- Не принимает решений "если тип X — делать Y" — это бизнес-логика сервиса
- Не вызывает инфраструктурные клиенты напрямую: не шлёт email, не пишет в Redis сам

```python
# ✅ Правильно — воркер передаёт управление сервису и не смотрит в содержимое
async def start(self) -> None:
    while self._running:
        task = await self._queue_service.dequeue(timeout=5)
        if task:
            await self._email_service.process(task)  # ← вся логика — в сервисе

# ❌ Неправильно — воркер сам разбирает задачу и принимает решения
async def start(self) -> None:
    while self._running:
        task = await self._queue_service.dequeue(timeout=5)
        if task["type"] == "verification_code":  # ← воркер знает о типах задач
            email = task["email"]                # ← воркер лезет в структуру задачи
            await self._smtp.send(email, ...)    # ← воркер вызывает инфру напрямую
```

---

### main.py — только сборка и запуск

`main.py` / `create_app()` — это точка сборки. Создаёт конфиг и контейнер, регистрирует роутеры, middleware, обработчики ошибок. Никаких решений, никакой логики.

**main.py делает:**
- Создаёт `Config` и `Container`
- Создаёт объект `FastAPI` и настраивает его параметры (title, version, default_response_class)
- Регистрирует middleware, роутеры, обработчики ошибок, lifespan-хуки
- Инициализирует и закрывает инфраструктуру в `lifespan`

**main.py никогда не делает:**
- Не содержит бизнес-логику или условия вида "если X — создавать Y"
- Не обращается к БД, Redis, S3 напрямую — только через контейнер в lifespan

```python
# ✅ Правильно — main только собирает уже готовые части
def create_app() -> FastAPI:
    cfg = Config.load()
    container = Container(cfg)
    app = FastAPI(title="Flokify", default_response_class=ORJSONResponse)
    app.include_router(auth_router, prefix="/api/v1")
    app.state.container = container
    return app

# ❌ Неправильно — main принимает решения
def create_app() -> FastAPI:
    cfg = Config.load()
    if cfg.app.ENV == "production":           # ← бизнес-условие в main
        container = ProdContainer(cfg)
    else:
        container = DevContainer(cfg)
    async with pool.acquire() as conn:        # ← прямая работа с БД в main
        await conn.execute("SELECT 1")
```

---

## 5. КОНВЕНЦИИ КОДА

### Именование

| Тип | Стиль | Пример |
|-----|-------|--------|
| Файлы и папки | `snake_case` | `user_repository.py`, `job_response/` |
| Классы | `PascalCase` | `PostgresUserRepository`, `JobService` |
| Функции и методы | `snake_case` | `get_current_user`, `fetch_row` |
| Переменные | `snake_case` | `job_id`, `hashed_password` |
| Константы | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE`, `_MAX_SEND_ATTEMPTS` |
| Интерфейсы (ABC) | `I` + `PascalCase` | `IUserRepository`, `IRedisClient` |
| Приватные атрибуты | `_underscore` | `self._query_executor`, `self._config` |
| Env-переменные | `UPPER_SNAKE_CASE` | `POSTGRES_HOST`, `JWT_SECRET_KEY` |
| Pydantic схемы запросов | `XxxRequest` | `JobCreateRequest`, `JobSearchRequest` |
| Pydantic схемы ответов | `XxxSchema` | `JobSchema`, `JobListSchema` |

### Структура файлов — порядок импортов

```python
# 1. Стандартная библиотека Python
from datetime import datetime
from typing import Annotated
from uuid import UUID

# 2. Внешние библиотеки
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

# 3. Внутренние модули (src.*)
from src.api.dependencies import get_job_service, get_verified_user
from src.api.v1.schemas.job import JobCreateRequest, JobSchema
from src.domain.entities.job import JobStatus
from src.services.job import JobService
```

### Структура файла роутера

```python
router = APIRouter(prefix="/resource", tags=["Tag"])

# Приватные хелперы (если нужны) — перед роутами
def _build_list_response(...): ...

# Роуты в порядке: POST /, GET /list, GET /{id}, PATCH /{id}, DELETE /{id}
@router.post("", response_model=Schema, status_code=status.HTTP_201_CREATED)
async def create_resource(...): ...
```

### __slots__ в классах

Все классы инфраструктуры и контейнеры используют `__slots__` для оптимизации:

```python
class PostgresUserRepository(IUserRepository):
    __slots__ = ("_query_executor",)
```

### Стиль кода (Ruff)

- `line-length = 120`
- `target-version = "py312"`
- Включены правила: `E, W, F, I, N, UP, B, C4, ARG, SIM, PTH, RET, RUF, PL`
- Двойные кавычки для строк
- Trailing commas в многострочных вызовах
- f-строки предпочтительны

---

## 6. ПАТТЕРНЫ И ПРИМЕРЫ

### Создание нового эндпоинта

```python
# ✅ Так принято в проекте (src/api/v1/routes/job.py)
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, status
from src.api.dependencies import get_verified_user, get_job_service
from src.api.v1.schemas.job import JobCreateRequest, JobSchema
from src.domain.entities.user import User
from src.services.job import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post(
    "",
    response_model=JobSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
        data: JobCreateRequest,
        current_user: Annotated[User, Depends(get_verified_user)],
        job_service: Annotated[JobService, Depends(get_job_service)],
):
    """Создать новую работу в статусе Draft"""
    job = await job_service.create_job(
        owner_id=current_user.id,
        title=data.title,
        # ...остальные поля явно по имени
    )
    return JobSchema.model_validate(job, from_attributes=True)


# ❌ Так НЕ делаем
@router.post("/jobs/create")  # Не используй /create в URL
async def create_job(request: Request):  # Не принимай сырой Request
    data = await request.json()  # Не парси JSON вручную
    job = JobService().create(data)  # Не создавай сервисы вручную
```

### Создание Pydantic-схемы

```python
# ✅ Так принято (src/api/v1/schemas/job.py)
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.domain.entities.job import JobCategory, JobStatus

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    price: float = Field(..., ge=0)
    category: JobCategory
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Tag length must not exceed 50 characters")
        return v

class JobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Обязательно для ответных схем
    id: UUID
    title: str
    status: JobStatus


# ❌ Так НЕ делаем
class JobSchema(BaseModel):
    class Config:          # Устаревший синтаксис Pydantic v1
        orm_mode = True
```

### Обработка ошибок в сервисе

```python
# ✅ Так принято (src/core/exceptions.py + сервисы)
from src.core.exceptions import NotFoundError, ForbiddenError, ConflictError

class JobService:
    async def get_job(self, job_id: str, user_id: str | None) -> JobView:
        job = await self._job_repository.get_by_id(job_id)
        if not job:
            raise NotFoundError("Работа не найдена")
        if not job.can_be_viewed_by(user_id):
            raise ForbiddenError("Нет доступа к этой работе")
        return job

    async def delete_job(self, job_id: str, owner_id: str) -> None:
        job = await self._job_repository.get_by_id(job_id)
        if not job:
            raise NotFoundError("Работа не найдена")
        job.assert_owner(owner_id)  # Кидает ForbiddenError если не владелец
        denial_reason = job.get_delete_denial_reason()
        if denial_reason:
            raise ConflictError(denial_reason)
        await self._job_repository.delete(job_id)


# ❌ Так НЕ делаем
async def get_job(self, job_id: str):
    try:
        job = await self._job_repository.get_by_id(job_id)
        return job
    except Exception as e:
        return None  # Не глотай ошибки, не возвращай None вместо исключения
```

### Создание репозитория

```python
# ✅ Так принято (src/infrastructure/postgres/repository/user_repository.py)
from src.domain.entities.user import User
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.user import IUserRepository

class PostgresUserRepository(IUserRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor):
        self._query_executor = query_executor

    async def get_by_id(self, user_id: str) -> User | None:
        query = """
            SELECT id, email, full_name, ...
            FROM users
            WHERE id = $1
        """
        row = await self._query_executor.fetch_row(query, user_id)
        if not row:
            return None
        return self._row_to_user(row)

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=str(row["id"]),
            email=row["email"],
            # ...все поля явно
        )


# ❌ Так НЕ делаем
# Никакого ORM (SQLAlchemy, Tortoise и т.д.) — только raw SQL через QueryExecutor
# Не использовать f-строки в SQL-запросах — только параметризованные запросы ($1, $2...)
async def get_by_id(self, user_id: str):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"  # SQL-инъекция!
```

### Добавление нового сервиса в контейнер

```python
# ✅ Паттерн из src/core/container/services.py

# 1. Добавить в __slots__
__slots__ = (..., "_my_new_service",)

# 2. Инициализировать как None в __init__
self._my_new_service: MyNewService | None = None

# 3. Создать lazy property
@property
def my_new_service(self) -> MyNewService:
    if not self._my_new_service:
        self._my_new_service = MyNewService(
            repo=self._repos.some_repository,
            logger=self._logger,
        )
    return self._my_new_service

# 4. Добавить зависимость в api/dependencies.py
async def get_my_new_service(
    container: Annotated[Container, Depends(get_container)],
) -> MyNewService:
    return container.services.my_new_service
```

### Создание интерфейса репозитория

```python
# ✅ Так принято (src/interfaces/repositories/user.py)
from abc import ABC, abstractmethod
from src.domain.entities.user import User

class IMyRepository(ABC):
    @abstractmethod
    async def create(self, field1: str, field2: int) -> MyEntity:
        """Описание метода"""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> MyEntity | None:
        raise NotImplementedError
```

### Доменная сущность

```python
# ✅ Так принято (src/domain/entities/job.py)
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class MyStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

@dataclass
class MyEntity:
    id: str
    owner_id: str
    status: MyStatus
    created_at: datetime

    # Бизнес-логика — методы на самой сущности
    def assert_owner(self, user_id: str) -> None:
        if self.owner_id != user_id:
            raise ForbiddenError("Нет доступа")

    def can_transition_to(self, new_status: MyStatus) -> bool:
        allowed = {MyStatus.DRAFT: [MyStatus.PUBLISHED]}
        return new_status in allowed.get(self.status, [])


# ❌ Так НЕ делаем
# Не добавлять SQL-запросы или импорты из infrastructure в доменные сущности
# Не использовать Pydantic BaseModel для доменных сущностей — только dataclass
```

### Добавление SQL-миграции

```sql
-- Файл: migrations/YYYYMMDD_NN_description.sql
-- Формат имени: 20260324_01_add-feature-table.sql

-- depends: 20260318_01_viewed-responses

CREATE TABLE my_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_my_table_user_id ON my_table(user_id);
```

```sql
-- Файл: migrations/YYYYMMDD_NN_description.rollback.sql
-- Обязательно создавать .rollback.sql для каждой миграции!
DROP TABLE IF EXISTS my_table;
```

### Rate limiting

```python
# ✅ Так принято (src/api/rate_limit.py + роуты)
from src.api.rate_limit import limiter
from fastapi import Request

@router.post("/register")
@limiter.limit("10/minute")
async def register(request: Request, data: RegisterRequest, ...):
    # request: Request обязательно должен быть первым параметром при использовании limiter
    ...
```

---

## 7. ЗАВИСИМОСТИ И ИНСТРУМЕНТЫ

### Ключевые библиотеки

| Библиотека | Назначение |
|-----------|-----------|
| `fastapi` | Web-фреймворк, роутинг, DI, OpenAPI |
| `granian` | ASGI-сервер (production, вместо uvicorn) |
| `asyncpg` | Асинхронный PostgreSQL-драйвер |
| `pydantic` + `pydantic-settings` | Валидация данных, конфигурация |
| `pyjwt` | JWT токены (HS256) |
| `argon2-cffi` | Хэширование паролей |
| `redis` | Кэш + task queue |
| `aioboto3` | Асинхронный S3/MinIO клиент |
| `loguru` | Структурированное логирование |
| `orjson` | Быстрая JSON-сериализация (default response class) |
| `slowapi` | Rate limiting (обёртка над limits) |
| `aiosmtplib` | Асинхронная отправка email (SMTP) |
| `httpx` | HTTP-клиент (для SSMS API) |
| `pillow` | Обработка изображений |
| `python-multipart` | Загрузка файлов (UploadFile) |
| `pyyaml` | Парсинг config.yaml |
| `yoyo-migrations` | SQL-миграции БД |
| `email-validator` | Валидация email через pydantic[email] |

### Инструменты разработки

| Инструмент | Назначение |
|-----------|-----------|
| `uv` | Менеджер пакетов (вместо pip/poetry) |
| `ruff` | Линтер + форматтер (вместо flake8 + isort + black) |

### Что НЕ добавлять (есть аналоги)

- ❌ `sqlalchemy`, `tortoise-orm`, `databases` — используем raw SQL через asyncpg
- ❌ `uvicorn` в production — используем granian
- ❌ `celery` — используем самодельный Redis worker
- ❌ `black`, `isort`, `flake8` — используем ruff
- ❌ `requests`, `aiohttp` — используем httpx
- ❌ `python-dotenv` — используем pydantic-settings

---

## 8. ФОРМАТ ОТВЕТОВ API

Все ответы через `ORJSONResponse` (установлен как `default_response_class`).

**Успешный ответ** — Pydantic-схема напрямую (FastAPI сериализует).

**Ошибка** — унифицированный формат из `exception_handlers.py`:
```json
{
    "status": "error",
    "code": "NOT_FOUND",
    "comment": "Работа не найдена",
    "obj": null
}
```

**Пагинация** (списки):
```json
{
    "jobs": [...],
    "total": 100,
    "limit": 50,
    "offset": 0
}
```

---

## 9. АУТЕНТИФИКАЦИЯ И АВТОРИЗАЦИЯ

### Зависимости в роутах

```python
# Только авторизованный пользователь (email может быть не подтверждён)
current_user: Annotated[User, Depends(get_current_user)]

# Авторизованный + email подтверждён (использовать везде кроме /auth)
current_user: Annotated[User, Depends(get_verified_user)]

# Авторизация опциональна (для публичных эндпоинтов с персонализацией)
current_user: Annotated[User | None, Depends(get_current_user_optional)]
```

### Токены
- Access token: Bearer JWT, expire 15 минут
- Refresh token: хранится в таблице `refresh_tokens`, expire 7 дней
- WebSocket auth: `?token=<access_token>` в query string

### Защита от брутфорса (email верификация)
- 5 неудачных попыток → блокировка на 30 минут
- Логика в `User.record_failed_attempt()` и `User.is_blocked()`

---

## 10. ВАЖНЫЕ ПРАВИЛА И ОГРАНИЧЕНИЯ

### НЕЛЬЗЯ:
- Использовать `f-строки` в SQL-запросах (SQL-инъекция) — только `$1, $2, ...`
- Импортировать `infrastructure` модули напрямую в `domain` или `services`
- Добавлять ORM поверх существующего Query Executor
- Обращаться к `os.environ` напрямую в сервисах — только через `Config`
- Читать `.env` в тестах вручную — конфиг должен пробрасываться через контейнер
- Создавать сервисы через `SomeService()` внутри роутов — только через `Depends()`
- Использовать `any` / `dict` без типов там, где есть типизированные альтернативы

### ОБЯЗАТЕЛЬНО:
- Каждой SQL-миграции — файл `.rollback.sql`
- Комментарий `-- depends:` в миграции, если она зависит от другой
- Интерфейс (ABC) для каждого репозитория и клиента
- `__slots__` в репозиториях, клиентах и контейнерах
- `model_config = ConfigDict(from_attributes=True)` в Pydantic-схемах ответов
- `from_attributes=True` при `model_validate()` для доменных сущностей
- Логировать ошибки 5xx через `logger.exception()`, предупреждения через `logger.warning()`
- `SecretStr` для секретных данных в конфиге (`.get_secret_value()` при использовании)

### Известные хаки / workarounds:
- `psycopg2-binary` в зависимостях — нужен только для yoyo-migrations (синхронный), в коде приложения asyncpg
- WebSocket получает контейнер через `websocket.app.state.container` (не через `Depends`), т.к. FastAPI DI не поддерживает WebSocket для некоторых зависимостей
- Lazy initialization в `ServiceContainer` защищена `if not self._service` (не `threading.Lock`) — достаточно для asyncio

### Технический долг:
- Отсутствуют тесты (unit и integration)
- Отсутствует CI/CD конфиг (GitHub Actions)
- README.md — шаблон, не отражает реальный проект
- Нет Sentry или аналога для мониторинга ошибок
- `LOG_FILE` в .env требует настройки пути для production контейнера

---

## 11. GIT-КОНВЕНЦИИ

### Текущее состояние
- Сообщения коммитов: в основном `fix`, `Update X.py` — нет чёткого стандарта
- Текущая ветка: `refactor-code`
- Main ветка: `main`

### Рекомендуемый формат (не обязателен, но желателен)
```
feat: добавить эндпоинт получения профиля пользователя
fix: исправить гонку состояний в S3Client.connect()
refactor: перенести логику верификации в домен
chore: обновить зависимости
```

---

## 12. CI/CD И ДЕПЛОЙ

### Деплой
CI/CD пайплайны отсутствуют.

**Production деплой вручную:**
```bash
# На сервере
git pull
docker-compose down
docker-compose up --build -d
```

**Миграции** применяются автоматически при старте контейнера `api` (CMD в Dockerfile):
```bash
yoyo apply --batch --database "postgresql://$POSTGRES_USER:..." ./migrations
```

### SSL-сертификаты
Лежат в `certs/`, монтируются в nginx.
