# Agent Guidelines for Safefood-Platform

## Project Overview

Food safety management platform with **FastAPI + SQLAlchemy 2.0 (async)** backend and **Vue 3 + TypeScript + Vite + Element Plus** frontend. Database: SQLite (dev), PostgreSQL/MySQL (prod).

---

## Build / Test Commands

### Backend (Python)

```bash
cd backend && pip install -r requirements.txt    # Install deps
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Dev server

# Testing (pytest configured in pytest.ini with asyncio_mode=auto)
pytest                                          # All tests
pytest tests/test_form_engine.py               # Single file
pytest tests/test_form_engine.py::test_missing_required_field    # Single test (RECOMMENDED)
pytest -k "test_acceptance"                     # Pattern match
pytest -v                                       # Verbose
pytest -vv -s                                   # Verbose + print output

# Migrations
alembic upgrade head                            # Apply migrations
alembic revision --autogenerate -m "message"   # Create migration
```

### Frontend (Vue 3 + TypeScript)

```bash
cd frontend/web-execution && npm install       # Install deps
npm run dev                                     # Development (Vite)
npm run build                                   # Build (vue-tsc + vite)
npm run preview                                 # Preview production build
# Same commands for frontend/web-admin
```

### Mobile (uni-app)

```bash
cd app-mobile/app-execution && npm install     # Install deps
npm run dev:h5                                  # H5 development
npm run dev:app                                 # App development
npm run build:h5                                # H5 build
npm run build:app                               # App build
# Same commands for app-mobile/app-admin
```

---

## Code Style Guidelines

### Python Backend

**Imports:** Standard library → third-party → local modules. Use absolute imports: `from app.modules.user.api import router`

**Type Hints:** Always use for parameters and return values. Use `Optional[X]` (not `X | None`). Use SQLAlchemy 2.0 style: `Mapped[X] = mapped_column(...)`

**Naming:** snake_case for variables/functions, PascalCase for classes, UPPER_SNAKE_CASE for constants, underscore prefix for private (`_internal_func`)

**SQLAlchemy Models:**
```python
class User(Base, TenantMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    __table_args__ = (UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),)
```

**Pydantic Schemas:** Use Pydantic v2 with `BaseModel`. Use `ConfigDict` for configuration:
```python
class LedgerResponse(BaseModel):
    id: int
    content: dict
    model_config = ConfigDict(from_attributes=True)
```

**Error Handling:** Use `HTTPException` for HTTP errors. Return consistent JSON using `GenericResponse`:
```python
class GenericResponse(BaseModel):
    code: int = 20000
    msg: str = "success"
    data: Optional[dict] = None
```

**Route Handlers:** Use dependency injection with `Depends()`:
```python
@router.get("/ledger/instances")
def get_ledger_instances(
    db: Session = Depends(get_sync_db),
):
```

**Async:** Use `async def` for async routes. Use `AsyncSession` for async DB operations:
```python
@router.get("/report/compilation")
async def get_compilation_report(
    db: AsyncSession = Depends(get_db),
):
```

**Multi-Tenancy:** Use `TenantMixin` for tenant-scoped models. Use `UserContext` for current tenant/user. Security guard prevents cross-tenant access.

---

### TypeScript / Vue Frontend

**Imports:** Use `@/` path alias. Order: Vue libraries → third-party → local imports.

**Naming:** camelCase for variables/functions/interfaces, PascalCase for components/types, UPPER_SNAKE_CASE for constants.

**TypeScript:** Always define interfaces for API requests/responses. Use strict typing; avoid `any`. Use generic types with axios.

```typescript
export interface UserQuery {
  page: number
  size: number
  keyword?: string
}

export function getUserList(params: UserQuery) {
  return request<{ records: UserItem[], total: number }>({
    url: '/users',
    method: 'get',
    params
  })
}
```

**Vue 3:** Use `<script setup lang="ts">`. Use `ref`, `reactive`, `computed` from Vue. Use Pinia stores with `defineStore`:

```typescript
export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const isLoggedIn = computed(() => !!token.value)
  return { token, isLoggedIn }
})
```

**Build:** `npm run build` runs `vue-tsc` for type checking before Vite build.

---

## Project Structure

```
backend/
├── app/
│   ├── api/           # API route registration
│   ├── core/          # Config, security, dependencies
│   │   ├── config.py
│   │   ├── deps.py    # Dependency injection
│   │   └── security/
│   ├── db/            # Session, models, mixins
│   │   ├── base.py
│   │   ├── mixins.py  # TenantMixin
│   │   └── session.py
│   └── modules/<name>/
│       ├── api.py     # Route handlers
│       ├── models.py  # SQLAlchemy models
│       ├── schemas.py # Pydantic schemas
│       ├── service.py # Business logic
│       └── exceptions.py
├── tests/             # Test files (test_*.py)
└── alembic/           # Migrations

frontend/
├── common/            # Shared components, utils, types
├── web-execution/src/ # Execution-side app
│   ├── api/           # API calls
│   ├── components/    # Reusable components
│   ├── views/         # Page components
│   ├── store/         # Pinia stores
│   └── utils/         # Utilities
└── web-admin/         # Admin-side app (same structure)

app-mobile/
├── common/            # Shared mobile components
├── app-execution/     # Execution-side App (uni-app)
└── app-admin/         # Admin-side App (uni-app)
```

---

## Key Patterns

**Multi-Tenancy:** Use `TenantMixin` for tenant-scoped models. Models are auto-registered in `TENANT_AWARE_MODELS`. Security guard enforces isolation.

**API Response Format:**
- Success: `{"code": 20000, "msg": "success", "data": {...}}`
- Error: `{"code": 40001, "msg": "error message", "data": null}`

**Database:** Development uses SQLite (`dev.db`). Always use Alembic migrations for schema changes.

**Environment Variables:**
```bash
# Backend .env
DATABASE_URL=sqlite+aiosqlite:///./dev.db
JWT_SECRET_KEY=your-secret-key
# Frontend (Vite)
VITE_APP_BASE_API=http://localhost:8000
```

**Headers:** Include `Authorization: Bearer <token>` and `X-App-Client` with API requests.

---

## Testing

- Place tests in `backend/tests/` with `test_*.py` naming
- Use `pytest` with `pytest-asyncio` for async tests (configured in `pytest.ini`)
- Run single test: `pytest tests/file.py::test_name` (most common)

```python
def test_missing_required_field() -> None:
    schema = {"fields": [{"field_id": "f_temp_01", "type": "number", "required": True}]}
    with pytest.raises(FieldValidationError) as excinfo:
        validate_data(schema, {})
    assert excinfo.value.field_id == "f_temp_01"
```

---

## Important Notes

1. **Multi-tenant isolation:** Always respect tenant boundaries via security guard
2. **Async only:** Backend is fully async; never use blocking operations
3. **Token handling:** Include `X-App-Client` header with API requests
4. **Database:** Use migrations for schema changes; never modify DB manually
5. **Frontend routing:** Use lazy loading for routes
6. **NEVER commit secrets:** Do not commit `.env`, `credentials.json`, or other sensitive files
7. **Pydantic v2:** Use `model_config = ConfigDict(...)` instead of `class Config`