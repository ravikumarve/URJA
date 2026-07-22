# URJA — Coding Standards & Contributing Guidelines

**Version**: 1.0
**Author**: Backend Architect + Frontend Developer
**Last Updated**: 2026-07-22
**Stack**: FastAPI (Python 3.12+) | PostgreSQL 16 / TimescaleDB | Next.js 16 | Tailwind v4 | shadcn/ui | Textual (TUI)

> These standards apply to **every** commit, **every** PR, and **every** file in the URJA monorepo. New contributors must read this document before writing code. Existing contributors must reference it during code review. There are no exceptions.

---

## Table of Contents

1. [Project Conventions](#1-project-conventions)
2. [Python / Backend Standards](#2-python--backend-standards)
3. [TypeScript / Frontend Standards](#3-typescript--frontend-standards)
4. [Testing Standards](#4-testing-standards)
5. [Documentation Standards](#5-documentation-standards)
6. [Environment & Configuration](#6-environment--configuration)
7. [PR & Review Checklist](#7-pr--review-checklist)
8. [Appendix: Quick Reference](#8-appendix-quick-reference)

---

## 1. Project Conventions

### 1.1 Git Workflow

URJA follows a simplified **trunk-based development** workflow with short-lived feature branches.

```
main  ──●────●────●────●────●────●────●────●──
          \    /      \    /      \    /
feature   └─●─┘       └─●─┘       └─●─┘
```

| Branch | Purpose | Source | Merges Into | Lifetime |
|--------|---------|--------|-------------|----------|
| `main` | Production-ready code | — | — | Infinite |
| `feature/*` | New feature or module | `main` | `main` via squash | Days, not weeks |
| `fix/*` | Bug fix | `main` | `main` via squash | Hours, not days |
| `docs/*` | Documentation only | `main` | `main` via squash | Hours |
| `chore/*` | Dependencies, tooling, config | `main` | `main` via squash | Hours |
| `release/*` | Release preparation | `main` | `main` via merge commit | Maintainer only |

**Rules:**
- Never commit directly to `main` — always open a PR.
- Keep branches short-lived (< 3 days). Stale branches are deleted after 14 days.
- Rebase onto `main` before opening a PR. Do not merge `main` into your branch — rebase.
- Squash-merge all feature/fix/docs/chore branches. Use merge commits only for `release/*`.

### 1.2 Conventional Commits

Every commit message must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**

| Type | When to Use | Version Impact |
|------|-------------|----------------|
| `feat` | New feature or module | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation only | PATCH |
| `style` | Formatting, whitespace, lint fixes | PATCH |
| `refactor` | Code change that neither fixes nor adds | PATCH |
| `perf` | Performance improvement | PATCH |
| `test` | Adding or fixing tests | PATCH |
| `chore` | Dependencies, build, CI, tooling | PATCH |
| `BREAKING CHANGE` | In body or footer, or append `!` after type/scope | MAJOR |

**Examples:**

```
feat(dispatch): add duck curve chart with price overlay

Implements the duck curve visualization on the Yield page,
overlaying generation, grid price, and curtailment on a 24-hour timeline.

Closes #142
```

```
fix(carbon): correct CO2e calculation for multi-asset batches

The emission factor was applied per-batch instead of per-asset,
causing overestimation for mixed-asset portfolios.

Fixes #189
```

```
chore(deps): upgrade fastapi from 0.110 to 0.115
```

```
refactor(api)!: rename telemetry ingest endpoint

BREAKING CHANGE: POST /api/v1/telemetry/ingest is now POST /api/v1/telemetry.
```

### 1.3 Branch Naming

Branches must follow the pattern: `<type>/<short-description>`

```
✅ feature/duck-curve-chart
✅ fix/revenue-calculation-race-condition
✅ docs/api-versioning-guide
✅ chore/update-arq-to-0.6

❌ fix-bug
❌ feature/THIS_IS_MY_NEW_FEATURE_THAT_IS_REALLY_COOL
❌ patch-1
❌ my-changes
```

Use kebab-case. Keep descriptions under 5 words. Use present tense.

### 1.4 Pull Request Process

**Every PR must include:**

1. **Title**: Follows conventional commit format: `type(scope): description`
2. **Description template:**

```markdown
## Summary
<!-- One paragraph explaining what this PR does and why -->

## Related Issues
Closes #NNN

## Type of Change
- [ ] feat (new feature)
- [ ] fix (bug fix)
- [ ] docs (documentation)
- [ ] refactor (no functional change)
- [ ] test (testing)
- [ ] chore (dependencies, build, CI)

## Testing
- [ ] Backend tests pass
- [ ] Frontend builds without errors
- [ ] Lint checks pass
- [ ] Manual testing performed (describe below)

## Screenshots (if UI change)

## Breaking Changes
<!-- If yes, describe migration path -->
```

3. **Review checklist**: Author must self-review against the checklist in Section 7.
4. **Size limit**: PRs should be < 400 lines changed. Large features must be broken into multiple PRs.

**Review flow:**
1. Author opens PR against `main`.
2. CI runs: lint → typecheck → test → build.
3. At least one maintainer approves.
4. CI must be green. Failing CI = no merge.
5. Author squash-merges (or maintainer merges for external contributors).

### 1.5 Version Numbering (SemVer)

URJA follows [Semantic Versioning 2.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

| Increment | When |
|-----------|------|
| **MAJOR** | Breaking API changes, database migrations requiring downtime, removal of features |
| **MINOR** | New features, new API endpoints, new modules, non-breaking additions |
| **PATCH** | Bug fixes, performance improvements, dependency updates, documentation |

**Pre-release tags:** `1.0.0-alpha.1`, `1.0.0-beta.2`, `1.0.0-rc.3`

**Current version:** `0.1.0` (pre-1.0 development — MINOR increments are frequent)

**Changelog:** Every release must have a corresponding entry in `CHANGELOG.md`. Entries are grouped by type (`feat`, `fix`, etc.) and link to the PR or commit.

---

## 2. Python / Backend Standards

### 2.1 Code Style

**Configuration:**
- **Formatter**: Ruff (line length 88, identical to Black defaults)
- **Linter**: Ruff with all rules enabled
- **Type checker**: mypy (strict mode)

Run before every commit:

```bash
ruff check .           # Lint
ruff format .          # Format
mypy src/              # Type check
```

**Ruff configuration** (in `pyproject.toml`):

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D203",    # Conflicts with D211 (one blank line before class docstring)
    "D213",    # Conflicts with D212 (multi-line docstring summary on second line)
    "EM101",   # Allow str in exceptions for simple cases
    "PLR0913", # Allow up to 5 args (ruff default handles this)
]

[tool.ruff.format]
docstring-code-format = true

[tool.mypy]
strict = true
python_version = "3.12"
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_return_any = true
warn_unused_ignores = true
```

**Line length:** 88 characters. No exceptions.

**String formatting:** f-strings exclusively. No `.format()` calls, no `%` formatting.

```python
# ✅ Good
name = f"{user.first_name} {user.last_name}"
log_msg = f"Asset {asset_id} curtailed {curtailed_kwh:.2f} kWh, revenue lost ${revenue_lost:.2f}"

# ❌ Bad
name = "{} {}".format(user.first_name, user.last_name)
log_msg = "Asset %s curtailed %.2f kWh" % (asset_id, curtailed_kwh)
```

**Path handling:** Use `pathlib.Path` exclusively. Never use `os.path`.

```python
# ✅ Good
from pathlib import Path

config_path = Path("config") / "settings.toml"
with config_path.open() as f:
    data = f.read()

# ❌ Bad
import os
config_path = os.path.join("config", "settings.toml")
with open(config_path) as f:
    data = f.read()
```

**Boolean comparisons:** Use `is` for `None`, `if x` for truthiness. Never compare to `True` or `False` with `==`.

```python
# ✅ Good
if user is None:
    raise HTTPException(status_code=404)
if not records:
    return []
if is_active:

# ❌ Bad
if user == None:
if len(records) == 0:
if is_active == True:
```

### 2.2 Type Hints

**Type hints are REQUIRED on ALL function signatures — no exceptions.**

This includes:
- Return types on every function
- Parameter types on every parameter
- Class attributes
- Module-level variables

```python
# ✅ Good
from collections.abc import Sequence
from uuid import UUID

from pydantic import BaseModel

from src.schemas.asset import AssetRead
from src.models.asset import Asset


async def list_assets(
    organization_id: UUID,
    site_id: UUID | None = None,
    asset_type: str | None = None,
    limit: int = 20,
) -> Sequence[AssetRead]:
    """List assets with optional filtering."""
    ...


ASSET_TYPES: dict[str, type[Asset]] = {
    "inverter": Inverter,
    "solar_panel": SolarPanel,
}


# ❌ Bad — missing return type, missing parameter types, untyped variable
async def list_assets(org_id, site_id=None):
    a = await get_assets(org_id)
    return a
```

**Use `T | None` syntax** (Python 3.10+) over `Optional[T]`:

```python
# ✅ Good (3.12 project)
def get_asset(asset_id: UUID) -> Asset | None:
    ...

# ❌ Bad
from typing import Optional
def get_asset(asset_id: UUID) -> Optional[Asset]:
    ...
```

**Use `Self` return type** for class methods returning `self`:

```python
from typing import Self

class AssetBuilder:
    def with_name(self, name: str) -> Self:
        self.name = name
        return self
```

**Use `TypedDict` for dictionary shapes (not raw dict):**

```python
from typing import TypedDict

class CurtailmentStats(TypedDict):
    total_curtailed_kwh: float
    total_revenue_lost: float
    event_count: int
```

### 2.3 Docstrings

**Google-style docstrings for all public APIs** (modules, classes, functions, methods).

```python
def calculate_health_score(
    asset_id: UUID,
    readings: Sequence[TelemetryReading],
    *,
    method: str = "z_score",
    threshold: float = 2.0,
) -> HealthScoreResult:
    """Compute a composite health score for an asset from its telemetry readings.

    Uses z-score anomaly detection on each metric (power, temperature, voltage),
    then combines them into a weighted 0–100 health score.

    Args:
        asset_id: The UUID of the asset to score.
        readings: Telemetry readings to analyze. Must contain at least
            ``window_size`` readings for meaningful results.
        method: Anomaly detection method. Defaults to ``z_score``.
        threshold: Z-score threshold for anomaly flagging.
            Values above this threshold trigger an alert.
            Defaults to 2.0 (standard deviation multiplier).

    Returns:
        A ``HealthScoreResult`` containing the composite score, per-metric
        scores, and any anomaly flags.

    Raises:
        ValueError: If ``readings`` is empty or ``window_size`` is less than 2.
        AssetNotFoundError: If ``asset_id`` does not exist.

    Example:
        >>> result = await calculate_health_score(
        ...     asset_id=UUID("abc123"),
        ...     readings=readings,
        ...     method="z_score",
        ...     threshold=3.0,
        ... )
        >>> result.health_score
        94.5
    """
    ...
```

**Rules:**
- Summary line: imperative mood, ends with period. Describe what the function does.
- `Args:` section: document every parameter. Include type info in prose if helpful.
- `Returns:` section: document return type and what it contains.
- `Raises:` section: document all expected exceptions.
- `Example:` section: optional but encouraged for complex functions.
- Internal/private functions (prefixed with `_`): short single-line docstring only.
- Module-level docstring at the top of every `.py` file.

### 2.4 Async Patterns

**All I/O operations must be async.** No blocking calls.

```python
# ✅ Good
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get("https://api.weather.example.com/forecast")

# ❌ Bad
import requests
response = requests.get("https://api.weather.example.com/forecast")
```

**Structured concurrency with `TaskGroup`** (Python 3.12+):

```python
# ✅ Good
from asyncio import TaskGroup

async def refresh_all_prices(sites: list[Site]) -> list[PriceResult]:
    async with TaskGroup() as tg:
        tasks = [tg.create_task(fetch_site_price(site)) for site in sites]
    return [task.result() for task in tasks]

# ❌ Bad — no error propagation, no cancellation
async def refresh_all_prices(sites: list[Site]) -> list[PriceResult]:
    tasks = [asyncio.create_task(fetch_site_price(site)) for site in sites]
    return await asyncio.gather(*tasks)
```

**`asyncio.timeout`** for all external API calls:

```python
# ✅ Good
from asyncio import timeout

async def fetch_weather(lat: float, lon: float) -> WeatherData:
    async with timeout(10.0):
        return await weather_client.get_forecast(lat, lon)
```

**Database sessions:** Always use `async with` context managers:

```python
# ✅ Good
async def get_asset(db: AsyncSession, asset_id: UUID) -> Asset | None:
    async with db.begin():
        result = await db.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

# ❌ Bad — session not properly managed
async def get_asset(db, asset_id):
    return await db.get(Asset, asset_id)
```

**ARQ tasks:** All task functions must be async and handle their own database sessions:

```python
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def telemetry_ingest_task(
    ctx: dict,
    batch_id: str,
    records: list[dict],
) -> dict:
    """Process a telemetry ingestion batch."""
    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    async with session_factory() as db:
        async with db.begin():
            # ... process records
            pass
    return {"batch_id": batch_id, "processed": len(records)}
```

### 2.5 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Functions | `snake_case` | `calculate_health_score()` |
| Variables | `snake_case` | `total_revenue_lost` |
| Classes | `PascalCase` | `CurtailmentEvent` |
| Modules/files | `snake_case` | `yield_optimizer.py` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_EMISSION_FACTOR` |
| Private helpers | `_leading_underscore` | `_validate_reading()` |
| Type variables | `short PascalCase` | `T`, `AssetT` |
| Enum members | `UPPER_SNAKE_CASE` | `Status.ACTIVE` |

**Pydantic model naming:**

```python
# Input schemas (request body)
class AssetCreate(BaseModel): ...
class TelemetryIngest(BaseModel): ...

# Output schemas (response)
class AssetRead(BaseModel): ...
class AssetList(BaseModel): ...

# Internal schemas
class HealthScoreResult(BaseModel): ...
```

### 2.6 Import Organization

Imports must be grouped in this exact order, separated by a blank line:

1. **Standard library**
2. **Third-party libraries**
3. **Local application**

Within each group, sort alphabetically.

```python
# ✅ Good
from collections.abc import Sequence
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db, require_admin
from src.models.asset import Asset
from src.schemas.asset import AssetCreate, AssetRead
from src.services.asset import create_asset

# ❌ Bad — wrong order, missing groups
from src.models.asset import Asset
import httpx
from uuid import UUID
import json
from fastapi import APIRouter
```

### 2.7 Error Handling

**Custom exception classes** — never raise bare `HTTPException` in service layer:

```python
# src/exceptions.py

class UrjaError(Exception):
    """Base exception for all URJA errors."""


class NotFoundError(UrjaError):
    """Resource not found."""


class ConflictError(UrjaError):
    """Resource already exists."""


class ValidationError(UrjaError):
    """Invalid input data."""


class AuthError(UrjaError):
    """Authentication or authorization failure."""
```

**Service layer** raises custom exceptions. **Routers** catch and convert to HTTP responses:

```python
# src/services/asset.py
async def get_asset(db: AsyncSession, asset_id: UUID) -> Asset:
    asset = await db.get(Asset, asset_id)
    if asset is None:
        raise NotFoundError(f"Asset {asset_id} not found")
    return asset


# src/routers/assets.py
@router.get("/{asset_id}", response_model=AssetRead)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    try:
        asset = await asset_service.get_asset(db, asset_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return AssetRead.model_validate(asset)
```

**Never bare `except Exception`:**

```python
# ✅ Good
try:
    result = await external_api.fetch_data()
except httpx.HTTPStatusError as e:
    logger.error("External API error: %s", e.response.text)
    raise ServiceUnavailableError("Weather API unavailable") from e

# ❌ Bad
try:
    result = await external_api.fetch_data()
except Exception:
    pass
```

**Always log with context:**

```python
import structlog

logger = structlog.get_logger(__name__)

# ✅ Good
logger.error(
    "Telemetry ingest failed",
    batch_id=batch_id,
    error=str(e),
    asset_count=len(records),
)

# ❌ Bad
logger.error(f"Telemetry ingest failed: {e}")
```

### 2.8 Project Structure

```
backend/
├── src/
│   ├── alembic/             # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── config.py            # Pydantic Settings
│   ├── database.py           # AsyncSession factory, engine
│   ├── dependencies.py       # FastAPI Depends() functions
│   ├── exceptions.py         # Custom exception classes
│   ├── logging_config.py     # Structured logging setup
│   ├── main.py               # FastAPI app factory
│   ├── middleware/           # Auth, CORS, rate limiting
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── rate_limit.py
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── asset.py
│   │   ├── telemetry.py
│   │   ├── curtailment.py
│   │   ├── carbon.py
│   │   └── ...
│   ├── routers/             # FastAPI APIRouter — thin!
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── assets.py
│   │   ├── telemetry.py
│   │   ├── dispatch.py
│   │   ├── carbon.py
│   │   ├── health.py
│   │   └── settings.py
│   ├── schemas/             # Pydantic v2 models
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── asset.py
│   │   ├── telemetry.py
│   │   └── ...
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── yield_optimizer.py
│   │   ├── carbon_vault.py
│   │   └── health_scorer.py
│   └── tasks/               # ARQ worker functions
│       ├── __init__.py
│       ├── telemetry_ingest.py
│       ├── carbon_mint.py
│       └── health_scan.py
├── tests/
│   ├── conftest.py          # Fixtures: db session, test client, factories
│   ├── factories/           # factory_boy factories
│   │   ├── __init__.py
│   │   ├── asset_factory.py
│   │   ├── telemetry_factory.py
│   │   └── ...
│   ├── routers/             # Tests mirror src/ structure
│   │   ├── test_assets.py
│   │   ├── test_telemetry.py
│   │   └── ...
│   └── services/
│       ├── test_yield_optimizer.py
│       └── ...
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

**Key rules:**
- **Routers are thin** — they parse the request, call a service, return a response. No business logic.
- **Services contain domain logic** — called by routers and tasks. Never depend on FastAPI.
- **Models are SQLAlchemy** — ORM entities with relationships. No business logic.
- **Schemas are Pydantic** — request/response validation. No business logic.
- **Tasks are ARQ workers** — background job functions. Each is independently testable.
- **Tests mirror `src/`** — `tests/routers/` tests routers, `tests/services/` tests services.

### 2.9 Router Guidelines

```python
# routers/assets.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db, require_admin, require_auth
from src.schemas.asset import AssetCreate, AssetList, AssetRead, AssetUpdate
from src.services import asset as asset_service

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=AssetList)
async def list_assets(
    site_id: UUID | None = None,
    asset_type: str | None = None,
    status: str | None = None,
    cursor: str | None = None,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
) -> AssetList:
    """List assets with filtering and pagination."""
    return await asset_service.list_assets(
        db=db,
        organization_id=current_user["org"],
        site_id=site_id,
        asset_type=asset_type,
        status=status,
        cursor=cursor,
        per_page=min(per_page, 100),
    )


@router.post("", response_model=AssetRead, status_code=201)
async def create_asset(
    body: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> AssetRead:
    """Create a new asset."""
    try:
        return await asset_service.create_asset(
            db=db,
            organization_id=current_user["org"],
            data=body,
        )
    except asset_service.ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

**Rules:**
- Every router function is `async def`.
- Use `Depends()` for all injected dependencies — never global state.
- Always return a `response_model` — never return raw dicts or ORM objects.
- Handle domain exceptions in the router and convert to HTTP errors.
- Parse query parameters, call service, return response. That's it.

### 2.10 SQLAlchemy Model Guidelines

```python
# models/asset.py
from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import String, Numeric, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSONB

from src.models.base import TimestampMixin, OrganizationMixin


class Asset(TimestampMixin, OrganizationMixin):
    __tablename__ = "assets"

    id: Mapped[UUID] = mapped_column(
        SA_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    site_id: Mapped[UUID] = mapped_column(
        SA_UUID(as_uuid=True), ForeignKey("asset_sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_asset_id: Mapped[UUID | None] = mapped_column(
        SA_UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"),
    )
    asset_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(100))
    capacity_kw: Mapped[float | None] = mapped_column(Numeric(12, 4))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active",
    )
    health_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    site = relationship("AssetSite", back_populates="assets")
    children = relationship("Asset", back_populates="parent", lazy="selectin")
```

**Rules:**
- Use `Mapped[]` with type annotations (SQLAlchemy 2.0 style).
- Use `UUID` primary keys with `uuid4()` default.
- Every table must have `organization_id` for tenant isolation.
- Use mixins for common columns (`created_at`, `updated_at`, `organization_id`).
- Never use `autocommit=True` — always manage sessions explicitly.

### 2.11 Pydantic Schema Guidelines

```python
# schemas/asset.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssetCreate(BaseModel):
    site_id: UUID
    parent_asset_id: UUID | None = None
    asset_type: str = Field(description="solar_panel, inverter, wind_turbine, battery_storage, meter")
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=100, pattern=r"^[A-Z0-9-]+$")
    capacity_kw: float | None = Field(None, gt=0)
    config: dict = Field(default_factory=dict)


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    asset_type: str
    name: str
    code: str
    status: str
    health_score: float | None
    capacity_kw: float | None
    created_at: datetime
    updated_at: datetime
```

**Rules:**
- Input schemas (`Create`, `Update`): use `Field()` for validation constraints.
- Output schemas (`Read`, `List`): use `model_config = ConfigDict(from_attributes=True)` for ORM mapping.
- Use `model_validate()` — never `from_orm()` (deprecated in v2).
- Use `field_validator` for custom validation logic:

```python
from pydantic import field_validator

class TelemetryIngest(BaseModel):
    records: list[TelemetryRecord]

    @field_validator("records")
    @classmethod
    def check_batch_size(cls, v: list) -> list:
        if len(v) > 1000:
            raise ValueError("Batch size cannot exceed 1000 records")
        return v
```

---

## 3. TypeScript / Frontend Standards

### 3.1 TypeScript Configuration

**`tsconfig.json` must include:**

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": false,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "incremental": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Key rules:**
- `strict: true` is **non-negotiable**.
- `noUncheckedIndexedAccess` prevents undefined-access bugs on arrays and records.
- `noImplicitReturns` ensures every code path returns a value.
- Path alias `@/*` for clean imports.

### 3.2 Component Architecture

**Function components + hooks only.** No class components anywhere in the codebase.

```tsx
// ✅ Good
function AssetDetail({ assetId }: { assetId: string }) {
  const { data, error } = useAsset(assetId);
  if (error) return <ErrorState message={error.message} />;
  if (!data) return <Skeleton className="h-96" />;
  return <AssetView asset={data} />;
}
```

**One component per file.** File name matches component name (PascalCase):

```
components/
  ui/
    KpiCard.tsx
    DataTable.tsx
    AlertBanner.tsx
  features/
    GenerationChart.tsx
    DuckCurveChart.tsx
    HealthGauge.tsx
    AssetMap.tsx
```

### 3.3 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Components | `PascalCase` | `KpiCard`, `GenerationChart` |
| Functions/variables | `camelCase` | `formatCurrency()`, `totalRevenue` |
| Files | `kebab-case` | `kpi-card.tsx`, `generation-chart.tsx` |
| Constants | `UPPER_SNAKE_CASE` | `API_BASE_URL`, `POLL_INTERVAL_MS` |
| Types/interfaces | `PascalCase` | `AssetData`, `HealthScoreResult` |
| CSS classes | Tailwind utilities only | — |

### 3.4 File Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout (Server Component)
│   │   ├── page.tsx            # Landing / dashboard redirect
│   │   ├── loading.tsx         # Root loading state
│   │   ├── error.tsx           # Root error boundary
│   │   ├── (auth)/             # Route group
│   │   │   ├── login/page.tsx
│   │   │   └── layout.tsx
│   │   ├── dashboard/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── loading.tsx
│   │   ├── assets/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   ├── yield/page.tsx
│   │   ├── carbon/page.tsx
│   │   ├── health/page.tsx
│   │   └── settings/page.tsx
│   ├── components/
│   │   ├── ui/                 # shadcn/ui + generic UI components
│   │   │   ├── kpi-card.tsx
│   │   │   ├── data-table.tsx
│   │   │   ├── alert-banner.tsx
│   │   │   └── ...
│   │   └── features/          # Domain-specific components
│   │       ├── generation-chart.tsx
│   │       ├── duck-curve-chart.tsx
│   │       ├── health-gauge.tsx
│   │       ├── asset-map.tsx
│   │       └── ...
│   ├── lib/                    # Utilities, API client, helpers
│   │   ├── api-client.ts       # Typed fetch wrapper
│   │   ├── utils.ts            # formatCurrency, cn(), etc.
│   │   └── types.ts            # Shared types
│   ├── hooks/                  # Custom React hooks
│   │   ├── use-asset.ts
│   │   ├── use-telemetry.ts
│   │   ├── use-auth.ts
│   │   └── ...
│   ├── contexts/               # React Context providers
│   │   ├── auth-context.tsx
│   │   ├── theme-context.tsx
│   │   └── notification-context.tsx
│   └── styles/
│       ├── globals.css         # Tailwind imports, custom base styles
│       └── ...
├── public/
│   └── ...
├── Dockerfile
├── next.config.ts
├── package.json
├── postcss.config.mjs
├── tailwind.config.ts
└── tsconfig.json
```

### 3.5 Server Components vs. Client Components

**Default to Server Components.** Only add `"use client"` when you need:

- React hooks (`useState`, `useEffect`, `useContext`, `useRef`, etc.)
- Browser APIs (`window`, `document`, `localStorage`, etc.)
- Event listeners (`onClick`, `onChange`, `onSubmit`, etc.)
- Third-party interactive libraries (Recharts, Leaflet, shadcn/ui interactive components)

```tsx
// ✅ app/dashboard/page.tsx — Server Component
import { getLatestTelemetry } from "@/lib/api-client";
import { GenerationKpiGrid } from "@/components/features/generation-kpi-grid";
import { DuckCurveChart } from "@/components/features/duck-curve-chart";

export const metadata = {
  title: "Dashboard | URJA",
};

export default async function DashboardPage() {
  const telemetry = await getLatestTelemetry();
  return (
    <div className="space-y-6">
      <GenerationKpiGrid data={telemetry} />
      <DuckCurveChart />
    </div>
  );
}
```

```tsx
// ✅ components/features/duck-curve-chart.tsx — Client Component (uses Recharts)
"use client";

import { Area, ComposedChart, Line, XAxis, YAxis } from "recharts";
import { useDuckCurve } from "@/hooks/use-duck-curve";

export function DuckCurveChart() {
  const { data, isLoading } = useDuckCurve();

  if (isLoading) return <Skeleton className="h-80 w-full" />;

  return (
    <ComposedChart data={data}>
      <XAxis dataKey="bucket" />
      <YAxis yAxisId="left" />
      <YAxis yAxisId="right" orientation="right" />
      <Area yAxisId="left" dataKey="avgGenerationKw" fill="hsl(var(--chart-1))" />
      <Line yAxisId="right" dataKey="avgPricePerKwh" stroke="hsl(var(--chart-2))" />
    </ComposedChart>
  );
}
```

**Push `"use client"` as deep as possible.** Prefer wrapping interactive leaves inside Server Component shells.

### 3.6 Data Fetching

**Use Server Components for initial data.** Never use `useEffect` for initial data fetching.

```tsx
// ✅ Good — Server Component fetches data, passes to Client Component
async function AssetPage({ params }: { params: { id: string } }) {
  const asset = await getAsset(params.id);
  return <AssetDetailView asset={asset} />;
}

// ❌ Bad — Client Component with useEffect for initial data
"use client";
function AssetPage({ params }: { params: { id: string } }) {
  const [asset, setAsset] = useState(null);
  useEffect(() => {
    fetch(`/api/assets/${params.id}`).then(r => r.json()).then(setAsset);
  }, [params.id]);
  if (!asset) return <Skeleton />;
  return <AssetDetailView asset={asset} />;
}
```

**For client-side data refetching** (polling, mutations), use SWR or a lightweight fetcher:

```tsx
// hooks/use-telemetry.ts
import useSWR from "swr";
import { apiClient } from "@/lib/api-client";

export function useLatestTelemetry(assetId?: string) {
  return useSWR(
    ["telemetry", "latest", assetId],
    () => apiClient.getLatestTelemetry(assetId),
    { refreshInterval: 15_000 },  // 15s polling
  );
}
```

**API client layer** — typed, with auth injection:

```ts
// lib/api-client.ts
type FetcherOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
};

export class ApiClientError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiClientError";
  }
}

export async function fetcher<T>(
  path: string,
  options: FetcherOptions = {},
): Promise<T> {
  const token = getAccessToken();  // from auth context
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiClientError(response.status, error.detail);
  }

  return response.json();
}
```

### 3.7 State Management

**React state + Context for v1.** No Redux, Zustand, or Jotai.

```tsx
// contexts/auth-context.tsx
"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

type User = {
  id: string;
  email: string;
  displayName: string;
  role: "admin" | "operator" | "viewer";
};

type AuthState = {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    const response = await fetcher<LoginResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    setUser(response.data.user);
    setAccessToken(response.data.accessToken);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setAccessToken(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isAuthenticated: user !== null,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
```

**Rules:**
- Use Context for auth, theme, and notifications only.
- Page-level state: `useState` or `useReducer`.
- Server state: SWR or Server Components.
- No global store for v1. If cross-component state becomes painful, add Zustand (lightweight, not Redux).

### 3.8 Styling

**Tailwind utility classes only.** No CSS modules, no styled-components, no `styled-jsx`.

```tsx
// ✅ Good
function KpiCard({ label, value, trend }: KpiCardProps) {
  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {trend && (
        <span className={cn(
          "text-sm",
          trend > 0 ? "text-green-600" : "text-red-600",
        )}>
          {trend > 0 ? "+" : ""}{trend}%
        </span>
      )}
    </div>
  );
}

// ❌ Bad
import styles from "./kpi-card.module.css";
function KpiCard() {
  return <div className={styles.card}>...</div>;
}
```

**Use `cn()` utility** from `@/lib/utils` for conditional classes:

```ts
// lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Dark mode:** Use Tailwind's `dark:` prefix. Leverage CSS variables from shadcn/ui theme.

**Responsive design:** Mobile-first. Test at 320px, 768px, 1024px, 1440px.

### 3.9 Accessibility

**Semantic HTML:**

```tsx
// ✅ Good
<main>
  <nav aria-label="Main navigation">
    <ul role="list">
      <li><a href="/dashboard">Dashboard</a></li>
    </ul>
  </nav>
  <section aria-labelledby="generation-heading">
    <h2 id="generation-heading">Generation Overview</h2>
    <div role="region" aria-live="polite">
      <KpiCard label="Current Generation" value="1,250 kW" />
    </div>
  </section>
</main>
```

**Checklist:**
- [ ] All images have `alt` text.
- [ ] Interactive elements have `aria-label` or visible text.
- [ ] Forms have proper `<label>` elements linked via `htmlFor`.
- [ ] Color is not the only indicator of meaning (add icons or text).
- [ ] Tab order follows visual order.
- [ ] Focus indicators are visible (Tailwind `focus-visible:ring-2`).
- [ ] `prefers-reduced-motion` respected for animations:

```tsx
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
```

- [ ] Role attributes on interactive custom elements (`role="button"`, `role="tab"`, etc.).

### 3.10 Performance

- Use `next/image` for **all** images — never raw `<img>`.
- Use `next/link` for **all** internal navigation — never `<a href>`.
- Add `loading.tsx` for every page with async data.
- Use `Suspense` with meaningful fallbacks:

```tsx
<Suspense fallback={<DashboardSkeleton />}>
  <DashboardContent />
</Suspense>
```

- Lazy-load below-fold components with `next/dynamic`:

```tsx
const AssetMap = dynamic(() => import("@/components/features/asset-map"), {
  loading: () => <Skeleton className="h-96 w-full" />,
});
```

- Never import server-only code (db, env secrets, fs) in Client Components.

### 3.11 TypeScript Type Patterns

```ts
// ✅ Use discriminated unions for API responses
type ApiResponse<T> =
  | { success: true; data: T; pagination?: Pagination }
  | { success: false; error: string };

// ✅ Use utility types instead of redefining shapes
type AssetUpdatePayload = Partial<Omit<AssetData, "id" | "createdAt" | "updatedAt">>;

// ✅ Use `as const` for literal constants
export const ASSET_TYPES = ["solar_panel", "inverter", "wind_turbine", "battery_storage", "meter"] as const;
export type AssetType = (typeof ASSET_TYPES)[number];

// ✅ Use type guards for runtime narrowing
function isAssetType(value: string): value is AssetType {
  return ASSET_TYPES.includes(value as AssetType);
}

// ❌ Bad — using any
function processData(data: any) {
  return data.assets.map((a: any) => a.name);
}

// ✅ Good — using unknown with type guard
function processData(data: unknown) {
  if (!isAssetListPayload(data)) throw new Error("Invalid payload");
  return data.assets.map((a) => a.name);
}
```

---

## 4. Testing Standards

### 4.1 Backend Tests (pytest)

**Configuration** (`pyproject.toml`):

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Structure:**

```
tests/
├── conftest.py              # Shared fixtures
├── factories/               # factory_boy factories
│   ├── asset_factory.py
│   ├── telemetry_factory.py
│   └── user_factory.py
├── routers/                 # API endpoint tests
│   ├── test_assets.py
│   ├── test_telemetry.py
│   ├── test_dispatch.py
│   ├── test_carbon.py
│   └── test_health.py
├── services/                # Service layer tests
│   ├── test_yield_optimizer.py
│   ├── test_carbon_vault.py
│   └── test_health_scorer.py
└── tasks/                   # ARQ task tests
    ├── test_telemetry_ingest.py
    └── test_carbon_mint.py
```

**Fixtures** (`conftest.py`):

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.main import create_app
from src.database import get_db


@pytest.fixture
async def db_session() -> AsyncSession:
    """Create a fresh test database session."""
    engine = create_async_engine("postgresql+asyncpg://urja:urja@localhost:5432/urja_test")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Test client with mocked DB session."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

**Test naming:** `test_{feature}_{scenario}`

```python
# ✅ Good
async def test_list_assets_returns_paginated_results(db_session, asset_factory):
async def test_create_asset_returns_409_on_duplicate_code(db_session, client):
async def test_calculate_health_score_raises_on_empty_readings():
async def test_ingest_telemetry_batch_returns_202_with_valid_payload(client):

# ❌ Bad
async def test_assets():
async def test_create():
async def test_1():
```

**Factory example:**

```python
# factories/asset_factory.py
import factory
from src.models.asset import Asset


class AssetFactory(factory.Factory):
    class Meta:
        model = Asset

    id = factory.Faker("uuid4")
    organization_id = factory.Faker("uuid4")
    site_id = factory.Faker("uuid4")
    name = factory.Sequence(lambda n: f"Inverter #{n}")
    code = factory.Sequence(lambda n: f"INV-{n:03d}")
    asset_type = "inverter"
    capacity_kw = 1500.0
    status = "active"
    health_score = 95.0
```

**Coverage:** Aim for 90%+ line coverage. Coverage config:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["src/alembic/*", "src/main.py", "src/config.py"]

[tool.coverage.report]
fail_under = 90
show_missing = true
```

### 4.2 Frontend Tests

**Component tests** with Vitest + React Testing Library:

```tsx
// components/__tests__/kpi-card.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { KpiCard } from "../ui/kpi-card";

describe("KpiCard", () => {
  it("renders the label and value", () => {
    render(<KpiCard label="Current Generation" value="1,250 kW" />);
    expect(screen.getByText("Current Generation")).toBeInTheDocument();
    expect(screen.getByText("1,250 kW")).toBeInTheDocument();
  });

  it("shows positive trend in green", () => {
    render(<KpiCard label="Revenue" value="$5,790" trend={12.5} />);
    const trend = screen.getByText("+12.5%");
    expect(trend).toHaveClass("text-green-600");
  });

  it("shows negative trend in red", () => {
    render(<KpiCard label="Revenue" value="$5,790" trend={-3.2} />);
    const trend = screen.getByText("-3.2%");
    expect(trend).toHaveClass("text-red-600");
  });
});
```

**E2E tests** with Playwright:

```ts
// e2e/dashboard.spec.ts
import { test, expect } from "@playwright/test";

test("dashboard loads generation KPIs", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByText("Current Generation")).toBeVisible();
  await expect(page.getByText("Total Revenue")).toBeVisible();
});

test("duck curve chart renders after data loads", async ({ page }) => {
  await page.goto("/dashboard");
  const chart = page.locator(".recharts-composed-wrapper");
  await expect(chart).toBeVisible({ timeout: 10000 });
});
```

### 4.3 CI Gate

Every PR must pass:

1. **Lint**: `ruff check .` — zero warnings, zero errors.
2. **Type check**: `mypy src/` — no type errors.
3. **Backend tests**: `pytest --cov=src --cov-fail-under=90`
4. **Frontend build**: `next build` — no errors.
5. **Frontend lint**: `next lint` — zero errors.
6. **Frontend tests**: `vitest run --coverage`
7. **E2E tests**: `npx playwright test` — all passing.

**Coverage must not decrease.** If code is added without tests, CI fails.

---

## 5. Documentation Standards

### 5.1 Inline Docstrings (Python)

See Section 2.3 above — Google-style docstrings on all public APIs.

### 5.2 README Files

- **Project root:** `README.md` — what URJA is, quick start, links to docs.
- **`/backend/README.md`** — backend architecture, environment setup, running tests.
- **`/frontend/README.md`** — frontend architecture, dev server, component patterns.
- **`/docs/development/README.md`** — link to this GUIDELINES.md, other dev docs.

### 5.3 Changelog

Every PR must include a changelog entry. The `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [0.2.0] - 2026-07-22

### Added
- Duck curve chart with price overlay (#142)
- Carbon credit portfolio summary endpoint (#167)

### Fixed
- CO2e calculation for multi-asset batches (#189)
- Session token rotation on refresh (#175)

### Changed
- Telemetry ingest endpoint from `/telemetry/ingest` to `/telemetry` (BREAKING)
- Upgrade FastAPI from 0.110 to 0.115

### Deprecated
- `/api/v1/curtailment/summary` — use `/api/v1/curtailment/revenue-lost`
```

### 5.4 Architecture Decision Records (ADRs)

All architectural decisions must be documented in `docs/development/ADRS.md`. Each ADR follows this template:

```markdown
# ADR-{NNN}: {Title}

**Date**: YYYY-MM-DD
**Status**: [Proposed | Accepted | Deprecated | Superseded]

## Context
What is the problem we are solving? What forces are at play?

## Decision
What did we decide and why? Include specific tools, patterns, or configurations.

## Consequences
What trade-offs, costs, or benefits come with this decision?

## Alternatives Considered
What else was considered and why was it rejected?
```

Reference ADRs from code comments when relevant:

```python
# ADR-007: 15s polling instead of WebSockets
# https://github.com/urja/urja/docs/development/ADRS.md#adr-007
```

---

## 6. Environment & Configuration

### 6.1 `.env.example` Template

Every environment variable must be documented in `.env.example`:

```bash
# =============================================================================
# URJA Environment Configuration
# Copy this file to .env and fill in secrets
# =============================================================================

# --- Database ---
DATABASE_URL=postgresql+asyncpg://urja:changeme@db:5432/urja
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# --- Redis ---
REDIS_URL=redis://redis:6379/0

# --- Auth ---
JWT_SECRET=change-me-to-a-random-64-char-string
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7

# --- API ---
CORS_ORIGINS=http://localhost:3000
API_RATE_LIMIT_PER_MINUTE=300
LOG_LEVEL=INFO

# --- External APIs ---
WEATHER_API_KEY=
WEATHER_API_BASE_URL=https://api.openweathermap.org/data/2.5
GRID_PRICE_API_KEY=
GRID_PRICE_API_BASE_URL=https://api.nordpoolgroup.com/dayahead
CARBON_REGISTRY_API_KEY=
CARBON_REGISTRY_API_BASE_URL=https://registry.verra.org/api

# --- Frontend ---
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png

# --- TUI ---
URJA_API_URL=http://api:8000/api/v1
URJA_POLL_INTERVAL=15
```

### 6.2 No Secrets in Code

**Absolute rule: Never commit secrets.**

```python
# ✅ Good — loaded from environment
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    jwt_secret: str
    database_url: str
    redis_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()

# ❌ Bad — hardcoded secrets
JWT_SECRET = "my-super-secret-key-12345"
DATABASE_URL = "postgresql+asyncpg://urja:password123@localhost:5432/urja"
```

### 6.3 Pydantic Settings

All configuration is managed through Pydantic Settings (`BaseSettings`):

```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://urja:urja@localhost:5432/urja"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    # API
    cors_origins: str = "http://localhost:3000"
    api_rate_limit_per_minute: int = 300
    log_level: str = "INFO"

    # External APIs
    weather_api_key: str = ""
    weather_api_base_url: str = "https://api.openweathermap.org/data/2.5"
    grid_price_api_key: str = ""
    grid_price_api_base_url: str = ""
    carbon_registry_api_key: str = ""
    carbon_registry_api_base_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()  # Singleton — import this everywhere
```

**Usage:**

```python
from src.config import settings

async def get_weather_forecast(lat: float, lon: float) -> WeatherData:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.weather_api_base_url}/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "appid": settings.weather_api_key,
            },
        )
        response.raise_for_status()
        return response.json()
```

---

## 7. PR & Review Checklist

### Author Self-Review Checklist

Before requesting review, verify:

#### Backend
- [ ] All function signatures have type hints (return type + all parameters).
- [ ] Google-style docstring on all public APIs.
- [ ] Ruff passes with zero warnings (`ruff check .`).
- [ ] mypy passes with strict mode (`mypy src/`).
- [ ] No bare `except Exception` — uses custom exceptions or specific exception types.
- [ ] All imports follow standard → third-party → local ordering.
- [ ] All async I/O uses `async/await` — no blocking calls.
- [ ] Database sessions use `async with` context managers.
- [ ] Pydantic schemas use `from_attributes=True` for output models.
- [ ] Router layer catches domain exceptions and converts to HTTP errors.
- [ ] New tables have `organization_id` and proper foreign key indexes.
- [ ] New models extend `TimestampMixin` and `OrganizationMixin`.
- [ ] Migration exists (Alembic) for any schema changes.
- [ ] New endpoints are documented (OpenAPI will auto-generate).
- [ ] Coverage >= 90% for new code.

#### Frontend
- [ ] TypeScript strict mode enabled — no `any`, no `!` without comment.
- [ ] Server Component by default — `"use client"` only where necessary.
- [ ] All images use `next/image` with `alt` text.
- [ ] All internal links use `next/link`.
- [ ] Tailwind utility classes only — no CSS modules.
- [ ] Semantic HTML elements used — div soup avoided.
- [ ] `aria-label` or visible text on all interactive elements.
- [ ] Dark mode supported via `dark:` prefix.
- [ ] `loading.tsx` exists for async pages.
- [ ] `error.tsx` exists for error boundaries.
- [ ] Component tests added for new components.
- [ ] `next build` passes with no errors.

#### General
- [ ] PR description follows template.
- [ ] Branch name follows `type/description` convention.
- [ ] Commit messages follow Conventional Commits.
- [ ] `.env.example` updated if new variables added.
- [ ] CHANGELOG entry added.
- [ ] ADR written for architectural decisions.
- [ ] No TODOs, FIXMEs, or debug code.
- [ ] No secrets, keys, or tokens in code or committed files.

### Reviewer Checklist

- [ ] Code follows all standards in this document.
- [ ] No obvious bugs or race conditions.
- [ ] Error handling covers expected failure modes.
- [ ] Tests cover the new code (not just happy path — also error cases and edge cases).
- [ ] Documentation is adequate (docstrings, README, CHANGELOG).
- [ ] No unnecessary complexity or over-engineering.
- [ ] Security review: no injection vectors, no secret leakage, proper auth checks.
- [ ] Performance review: no N+1 queries, no missing indexes, no blocking calls.

---

## 8. Appendix: Quick Reference

### 8.1 Common Commands

```bash
# Backend
ruff check .                    # Lint
ruff check --fix .              # Auto-fix lint issues
ruff format .                   # Format code
mypy src/                       # Type check
pytest                          # Run tests
pytest --cov=src --cov-report=term-missing  # Coverage report

# Frontend
npm run dev                     # Start dev server
npm run build                   # Production build
npm run lint                    # Lint
npm run typecheck               # Type check (tsc --noEmit)
npm test                        # Run component tests
npx playwright test             # Run E2E tests

# Database
alembic upgrade head            # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration

# Docker
docker compose up -d            # Start all services
docker compose logs -f api      # Follow API logs
docker compose exec db psql -U urja  # Open database shell
```

### 8.2 Code Review Flowchart

```
                    ┌─────────────┐
                    │  Open PR    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  CI Runs    │
                    └──────┬──────┘
                           ▼
                  ┌────────────────┐
                  │ CI Passes?     │
                  └────┬───┬───────┘
                       │   │
                      Yes  No ──→ Fix and push
                       │
                       ▼
                  ┌────────────────┐
                  │ Review        │
                  │ Requested     │
                  └────┬───┬──────┘
                       │   │
                  ┌────┘   └────┐
                  ▼              ▼
            ┌──────────┐  ┌──────────┐
            │ Approve  │  │ Changes  │
            └────┬─────┘  │ Requested│
                 │        └────┬─────┘
                 │             │
                 │        ┌────▼────┐
                 │        │ Author  │
                 │        │ Fixes   │
                 │        └────┬────┘
                 │             │
                 └──────┬──────┘
                        ▼
                 ┌──────────────┐
                 │ Squash Merge │
                 │ into main    │
                 └──────────────┘
```

### 8.3 Git Config

Recommended global git config for URJA contributors:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global pull.rebase true
git config --global rebase.autoStash true
git config --global init.defaultBranch main
```

### 8.4 Recommended VS Code Extensions

| Extension | Purpose |
|-----------|---------|
| ms-python.python | Python language support |
| ms-python.vscode-pylance | Type checking in editor |
| charliermarsh.ruff | Ruff integration (lint + format) |
| dbaeumer.vscode-eslint | ESLint for TypeScript |
| esbenp.prettier-vscode | Prettier formatter |
| bradlc.vscode-tailwindcss | Tailwind CSS intellisense |
| github.vscode-github-actions | GitHub Actions viewer |
| redhat.vscode-yaml | YAML validation |

### 8.5 Pre-commit Hook

Install via `pre-commit`:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy, httpx, structlog]
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        types_or: [javascript, jsx, typescript, tsx, json, css, markdown]
```

### 8.6 Related Documents

- [ARCHITECTURE.md](../technical/ARCHITECTURE.md) — System architecture (C4 model)
- [API-SPEC.md](../technical/API-SPEC.md) — Complete API reference
- [DATABASE.md](../technical/DATABASE.md) — Database schema and TimescaleDB configuration
- [PRD.md](../product/PRD.md) — Product requirements
- [DEPLOYMENT.md](../technical/DEPLOYMENT.md) — Deployment guide
- [SECURITY.md](../technical/SECURITY.md) — Security architecture
- [CHANGELOG.md](../development/CHANGELOG.md) — Release history
- [ADRS.md](../development/ADRS.md) — Architecture Decision Records
