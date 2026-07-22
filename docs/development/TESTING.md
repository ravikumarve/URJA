# URJA — Testing Strategy

**Version**: 1.0
**Author**: Test Automation Engineer
**Last Updated**: 2026-07-22
**Stack**: pytest 8.x + pytest-asyncio | Playwright 1.50+ | factory_boy | Vitest + RTL

> This document defines the complete testing strategy for the URJA monorepo. Every test decision — from fixture design to flake management — is documented here. A flaky test is a bug with your name on it. Deterministic, isolated, fast: you do not get to pick two.

---

## Table of Contents

1. [Testing Philosophy](#1-testing-philosophy)
2. [Backend Testing (pytest)](#2-backend-testing-pytest)
3. [Frontend Testing (Playwright)](#3-frontend-testing-playwright)
4. [Component Testing (Vitest)](#4-component-testing-vitest)
5. [Test Data Strategy](#5-test-data-strategy)
6. [CI Integration](#6-ci-integration)
7. [Flake Management](#7-flake-management)
8. [Testing Commands Reference](#8-testing-commands-reference)
9. [Testing Checklist (for PRs)](#9-testing-checklist-for-prs)
10. [Appendix: File Reference](#10-appendix-file-reference)

---

## 1. Testing Philosophy

### 1.1 The Test Pyramid

URJA follows a strict test pyramid with three layers:

```
         ┌──────┐
         │ E2E  │  ← Few. Critical user journeys only.
        ┌┴──────┴┐
        │Integr. │  ← API + database end-to-end. Service boundaries.
       ┌┴────────┴┐
       │   Unit   │  ← Many. Service logic with mocked I/O.
       └──────────┘
```

| Layer | Count Target | Speed | What It Covers |
|-------|-------------|-------|----------------|
| **Unit** | ~70% of tests | < 5ms each | Service logic, algorithms, validation, error handling |
| **Integration** | ~25% of tests | < 500ms each | API endpoints with real DB, ARQ tasks with real Redis |
| **E2E** | ~5% of tests | < 30s each | Critical user journeys in the browser |

### 1.2 What Goes Where

**Unit tests** (`tests/services/`, `tests/tasks/`):
- Yield optimizer curtailment detection logic
- Carbon vault CO2e calculation algorithm
- Health scorer z-score anomaly detection
- Pydantic schema validation rules
- Repository pattern with mocked `AsyncSession`
- Pure function utilities and helpers

**Integration tests** (`tests/routers/`, `tests/integration/`):
- Every API endpoint: happy path + error cases + auth failures
- Database operations: hypertable inserts, continuous aggregate queries
- ARQ task execution with real Redis + real DB
- External client mocking (weather API, grid pricing, carbon registry)

**E2E tests** (`frontend/e2e/`):
- Login → Dashboard (6 KPI cards visible)
- Dashboard → Assets → Map → Marker detail
- Dashboard → Carbon → Credits table → Filter by status
- Dashboard → Health → Alerts → Acknowledge → Confirmed
- Settings → API key management

### 1.3 The E2E Reserve Rule

> "Reserve E2E for journeys where the integration itself is the risk."

The integration of frontend + backend is the risk. Rendering a single component is not — that is the job of Vitest + RTL. A flaky E2E test is more expensive than a flaky unit test by orders of magnitude: it takes longer to run, harder to debug, and blocks CI for everyone.

**When to write E2E:**
- The journey touches 3+ distinct components (e.g., auth → dashboard → asset detail)
- The journey involves real API calls with auth tokens
- The journey produces side effects (credit minting, alert acknowledgment)
- The journey is a release-blocking flow (login, dashboard load, navigation)

**When to write component tests instead:**
- A single component renders correctly with props
- A component handles loading/error/empty states
- A form validates fields correctly
- A chart renders with given data

### 1.4 Determinism Rules

1. **No test depends on another test's data.** Every test gets a fresh database.
2. **No hard-coded IDs.** Always use factories to create references.
3. **No `time.sleep()`.** Use `await asyncio.wait_for()`, `page.waitForSelector()`, or explicit polling.
4. **No shared mutable state.** If a fixture modifies global state, it must yield and clean up.
5. **Seeds are deterministic.** `factory.Faker` uses a fixed seed in tests.

---

## 2. Backend Testing (pytest)

### 2.1 pytest Configuration

```toml
# backend/pyproject.toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:alembic.*",
    "ignore::DeprecationWarning:sqlalchemy.*",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "timescaledb: marks tests requiring TimescaleDB (skipped in CI)",
    "integration: marks integration tests (DB + Redis)",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "src/alembic/*",
    "src/main.py",
    "src/config.py",
    "src/logging_config.py",
]

[tool.coverage.report]
fail_under = 90
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "@overload",
]

[tool.coverage.html]
directory = "htmlcov"
```

### 2.2 Test Directory Structure

```
backend/tests/
├── conftest.py                 # Global fixtures: db, client, auth, factories
├── factories/                  # factory_boy factories
│   ├── __init__.py
│   ├── asset_factory.py
│   ├── user_factory.py
│   ├── organization_factory.py
│   ├── telemetry_factory.py
│   ├── curtailment_factory.py
│   ├── carbon_factory.py
│   ├── health_factory.py
│   └── dispatch_factory.py
├── routers/                    # API endpoint tests (mirrors src/routers/)
│   ├── conftest.py             # Router-specific fixtures
│   ├── test_auth.py
│   ├── test_assets.py
│   ├── test_telemetry.py
│   ├── test_dispatch.py
│   ├── test_carbon.py
│   └── test_health.py
├── services/                   # Service layer unit tests
│   ├── test_yield_optimizer.py
│   ├── test_carbon_vault.py
│   └── test_health_scorer.py
├── tasks/                      # ARQ task tests
│   ├── test_telemetry_ingest.py
│   ├── test_carbon_mint.py
│   └── test_health_scan.py
├── integration/                # Cross-cutting integration tests
│   ├── test_hypertable.py
│   ├── test_continuous_aggregates.py
│   └── test_full_ingestion_pipeline.py
└── models/                     # Model and repository tests
    ├── test_asset_repo.py
    └── test_telemetry_repo.py
```

### 2.3 Core Fixtures (`conftest.py`)

```python
# backend/tests/conftest.py
from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.database import get_db
from src.main import create_app
from src.config import settings as test_settings

TEST_DATABASE_URL = (
    "postgresql+asyncpg://urja:urja@localhost:5432/urja_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop per session for all async fixtures."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create engine once per session. Drops and recreates all tables."""
    from src.models import Base

    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession]:
    """Fresh transaction per test, rolled back after."""
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession,
    )
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient]:
    """Test client with dependency overrides for DB session and auth."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    default_user: dict,
) -> AsyncGenerator[AsyncClient]:
    """Client pre-authenticated with a valid JWT token."""
    from src.auth.jwt import create_access_token

    token = create_access_token(
        sub=default_user["id"],
        org=default_user["organization_id"],
        roles=[default_user["role"]],
    )
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
```

### 2.4 Factory Boy Factories

```python
# backend/tests/factories/asset_factory.py
import factory
from factory import Faker
from uuid import uuid4


class AssetFactory(factory.DictFactory):
    id = factory.LazyFunction(uuid4)
    organization_id = factory.LazyFunction(uuid4)
    site_id = factory.LazyFunction(uuid4)
    name = factory.Sequence(lambda n: f"Inverter #{n}")
    code = factory.Sequence(lambda n: f"INV-{n:03d}")
    asset_type = "inverter"
    serial_number = Faker("bothify", text="SMA-????-####")
    manufacturer = "SMA Solar Technology"
    model = "Sunny Central 2200-US"
    capacity_kw = 1500.0
    latitude = Faker("latitude")
    longitude = Faker("longitude")
    status = "active"
    health_score = 95.0
    config = {}
    metadata = {}
    created_at = Faker("date_time_this_year")
    updated_at = Faker("date_time_this_year")


class TelemetryReadingFactory(factory.DictFactory):
    asset_id = factory.LazyFunction(uuid4)
    organization_id = factory.LazyFunction(uuid4)
    ts = Faker("date_time_this_month")
    generation_kw = Faker("pyfloat", min_value=0, max_value=2000)
    energy_kwh = Faker("pyfloat", min_value=0, max_value=500)
    power_factor = Faker("pyfloat", min_value=0.8, max_value=1.0)
    voltage_v = Faker("pyfloat", min_value=460, max_value=500)
    current_a = Faker("pyfloat", min_value=0, max_value=3000)
    temperature_c = Faker("pyfloat", min_value=20, max_value=60)
    quality_code = 0
    ingested_at = Faker("date_time_this_month")


class CarbonCreditFactory(factory.DictFactory):
    credit_id = factory.LazyFunction(uuid4)
    batch_id = factory.LazyFunction(uuid4)
    asset_id = factory.LazyFunction(uuid4)
    organization_id = factory.LazyFunction(uuid4)
    status = "active"
    quantity = 1.0
    unit = "tCO2e"
    methodology = "IPMVP_v2.1"
    total_kwh = 1087.0
    emission_factor = 0.92
    notes = ""
    metadata = {}
```

### 2.5 API Test Patterns

```python
# backend/tests/routers/test_assets.py
from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.factories.asset_factory import AssetFactory


class TestListAssets:
    async def test_returns_paginated_results(
        self, authenticated_client: AsyncClient, db_session,
    ):
        response = await authenticated_client.get("/api/v1/assets")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "pagination" in body

    async def test_filters_by_asset_type(
        self, authenticated_client: AsyncClient, db_session,
    ):
        response = await authenticated_client.get(
            "/api/v1/assets?asset_type=inverter",
        )
        assert response.status_code == 200
        for asset in response.json()["data"]:
            assert asset["asset_type"] == "inverter"

    async def test_returns_401_without_auth(
        self, client: AsyncClient,
    ):
        response = await client.get("/api/v1/assets")
        assert response.status_code == 401

    async def test_returns_422_on_invalid_filter(
        self, authenticated_client: AsyncClient,
    ):
        response = await authenticated_client.get(
            "/api/v1/assets?per_page=999",
        )
        assert response.status_code == 422

    async def test_pagination_cursor_works(
        self, authenticated_client: AsyncClient,
    ):
        page1 = await authenticated_client.get(
            "/api/v1/assets?per_page=1",
        )
        assert page1.status_code == 200
        data1 = page1.json()
        if data1["pagination"]["has_more"]:
            next_cursor = data1["pagination"]["next_cursor"]
            page2 = await authenticated_client.get(
                f"/api/v1/assets?cursor={next_cursor}&per_page=1",
            )
            assert page2.status_code == 200
            assert len(page2.json()["data"]) > 0


class TestCreateAsset:
    async def test_creates_asset_with_valid_data(
        self, authenticated_client: AsyncClient,
    ):
        payload = AssetFactory.build()
        response = await authenticated_client.post(
            "/api/v1/assets", json=payload,
        )
        assert response.status_code == 201
        created = response.json()["data"]
        assert created["name"] == payload["name"]
        assert created["code"] == payload["code"]

    async def test_returns_409_on_duplicate_code(
        self, authenticated_client: AsyncClient, db_session,
    ):
        existing = AssetFactory.build()
        await authenticated_client.post("/api/v1/assets", json=existing)
        response = await authenticated_client.post(
            "/api/v1/assets", json=existing,
        )
        assert response.status_code == 409

    async def test_returns_422_on_missing_required_field(
        self, authenticated_client: AsyncClient,
    ):
        payload = AssetFactory.build()
        del payload["name"]
        response = await authenticated_client.post(
            "/api/v1/assets", json=payload,
        )
        assert response.status_code == 422

    async def test_returns_403_with_viewer_role(
        self, client: AsyncClient, viewer_token: str,
    ):
        client.headers["Authorization"] = f"Bearer {viewer_token}"
        payload = AssetFactory.build()
        response = await client.post("/api/v1/assets", json=payload)
        assert response.status_code == 403
```

### 2.6 Service Layer Unit Tests

```python
# backend/tests/services/test_yield_optimizer.py
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from src.services.yield_optimizer import (
    detect_curtailment,
    calculate_revenue_lost,
    optimize_dispatch,
)


class TestDetectCurtailment:
    async def test_detects_curtailment_below_threshold(self):
        readings = [
            {"generation_kw": 100.0, "expected_kw": 1000.0},
            {"generation_kw": 120.0, "expected_kw": 1000.0},
            {"generation_kw": 90.0, "expected_kw": 1000.0},
        ]
        result = await detect_curtailment(readings, threshold_pct=20)
        assert result.is_curtailed is True
        assert result.avg_deviation_pct > 80

    async def test_returns_false_when_generation_normal(self):
        readings = [
            {"generation_kw": 950.0, "expected_kw": 1000.0},
            {"generation_kw": 980.0, "expected_kw": 1000.0},
            {"generation_kw": 960.0, "expected_kw": 1000.0},
        ]
        result = await detect_curtailment(readings, threshold_pct=20)
        assert result.is_curtailed is False

    async def test_requires_minimum_readings(self):
        readings = [{"generation_kw": 100.0, "expected_kw": 1000.0}]
        with pytest.raises(ValueError, match="minimum"):
            await detect_curtailment(readings)

    async def test_detection_window_configurable(self):
        readings = [
            {"generation_kw": 50.0, "expected_kw": 1000.0},
            {"generation_kw": 60.0, "expected_kw": 1000.0},
        ]
        result = await detect_curtailment(
            readings, threshold_pct=20, window_size=2,
        )
        assert result.is_curtailed is True


class TestCalculateRevenueLost:
    async def test_calculates_correct_revenue(self):
        result = await calculate_revenue_lost(
            curtailed_kwh=Decimal("1425.0"),
            price_per_kwh=Decimal("0.12"),
        )
        assert result == Decimal("171.00")

    async def test_returns_zero_when_no_curtailment(self):
        result = await calculate_revenue_lost(
            curtailed_kwh=Decimal("0"),
            price_per_kwh=Decimal("0.12"),
        )
        assert result == Decimal("0")


class TestOptimizeDispatch:
    async def test_charges_battery_when_price_below_threshold(self):
        decision = await optimize_dispatch(
            current_price=Decimal("0.05"),
            price_threshold=Decimal("0.08"),
            battery_soc=30,
        )
        assert decision.action == "charge_battery"

    async def test_discharges_battery_when_price_above_threshold(self):
        decision = await optimize_dispatch(
            current_price=Decimal("0.35"),
            price_threshold=Decimal("0.30"),
            battery_soc=80,
        )
        assert decision.action == "discharge_battery"
```

### 2.7 Database Integration Tests

```python
# backend/tests/integration/test_hypertable.py
import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

skip_if_ci = pytest.mark.skipif(
    os.getenv("CI", "").lower() == "true",
    reason="TimescaleDB not available in CI",
)


@skip_if_ci
class TestTelemetryHypertable:
    async def test_insert_and_query_generation_readings(
        self, db_session: AsyncSession,
    ):
        await db_session.execute(
            text("""
                INSERT INTO telemetry_generation (ts, asset_id, organization_id, generation_kw)
                VALUES (now(), '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 1500.0)
            """),
        )
        await db_session.commit()
        result = await db_session.execute(
            text("SELECT count(*) FROM telemetry_generation"),
        )
        count = result.scalar()
        assert count == 1

    async def test_hypertable_chunk_interval_configurable(
        self, db_session: AsyncSession,
    ):
        result = await db_session.execute(
            text("""
                SELECT chunk_time_interval
                FROM _timescaledb_catalog.hypertable
                WHERE table_name = 'telemetry_generation'
            """),
        )
        interval = result.scalar()
        assert interval is not None


@skip_if_ci
class TestContinuousAggregates:
    async def test_hourly_aggregate_refreshes(
        self, db_session: AsyncSession,
    ):
        result = await db_session.execute(
            text("""
                SELECT count(*) FROM hourly_generation
            """),
        )
        count = result.scalar()
        assert count >= 0

    async def test_daily_aggregate_refreshes_from_hourly(
        self, db_session: AsyncSession,
    ):
        result = await db_session.execute(
            text("""
                SELECT count(*) FROM daily_generation
            """),
        )
        count = result.scalar()
        assert count >= 0
```

### 2.8 Task Worker Tests

```python
# backend/tests/tasks/test_telemetry_ingest.py
from uuid import uuid4

import pytest
from asyncio import timeout as async_timeout

from src.tasks.telemetry_ingest import process_ingest_batch


class TestTelemetryIngestTask:
    async def test_processes_valid_batch(
        self, db_session, task_context,
    ):
        batch_id = str(uuid4())
        records = [
            {
                "asset_id": str(uuid4()),
                "ts": "2026-07-22T12:00:00Z",
                "generation_kw": 1250.5,
                "energy_kwh": 312.6,
                "quality_code": 0,
            },
        ]
        async with async_timeout(5):
            result = await process_ingest_batch(
                task_context, batch_id=batch_id, records=records,
            )
        assert result["batch_id"] == batch_id
        assert result["records_accepted"] == 1
        assert result["records_rejected"] == 0

    async def test_rejects_malformed_records(
        self, db_session, task_context,
    ):
        records = [
            {
                "asset_id": "not-a-uuid",
                "ts": "invalid-date",
                "generation_kw": -100,
            },
        ]
        async with async_timeout(5):
            result = await process_ingest_batch(
                task_context, batch_id=str(uuid4()), records=records,
            )
        assert result["records_accepted"] == 0
        assert result["records_rejected"] == 1
```

---

## 3. Frontend Testing (Playwright)

### 3.1 Playwright Configuration

```typescript
// frontend/playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : 1,
  reporter: [
    ["html", { outputFolder: "playwright-report" }],
    ["json", { outputFile: "playwright-report/results.json" }],
    ["list"],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "on-first-retry",
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
  ],
});
```

### 3.2 Auth Setup — Login Once via API

Never log in through the UI form in every test. Use Playwright's storage state to authenticate once:

```typescript
// frontend/e2e/auth.setup.ts
import { test as setup, expect } from "@playwright/test";

const AUTH_FILE = "playwright/.auth/user.json";

setup("authenticate via API", async ({ request }) => {
  const response = await request.post(
    `${process.env.NEXT_PUBLIC_API_URL}/auth/login`,
    {
      data: {
        email: "admin@urja-test.com",
        password: "test-password-123",
      },
    },
  );
  expect(response.ok()).toBeTruthy();
  const body = await response.json();

  // Store tokens for use in tests
  await request.storageState({
    path: AUTH_FILE,
    state: {
      cookies: [
        {
          name: "refresh_token",
          value: body.data.refresh_token,
          domain: "localhost",
          path: "/",
          httpOnly: true,
          secure: false,
          sameSite: "Strict",
        },
      ],
      origins: [
        {
          origin: "http://localhost:3000",
          localStorage: [
            {
              name: "access_token",
              value: body.data.access_token,
            },
          ],
        },
      ],
    },
  });
});
```

```typescript
// frontend/playwright.config.ts — add projects
projects: [
  {
    name: "setup",
    testMatch: /auth\.setup\.ts/,
  },
  {
    name: "chromium",
    dependencies: ["setup"],
    use: {
      ...devices["Desktop Chrome"],
      storageState: "playwright/.auth/user.json",
    },
  },
  // ...
]
```

### 3.3 Page Object Model

```typescript
// frontend/e2e/pages/dashboard-page.ts
import { type Locator, type Page, expect } from "@playwright/test";

export class DashboardPage {
  readonly page: Page;
  readonly kpiCards: Locator;
  readonly duckCurveChart: Locator;
  readonly assetMap: Locator;
  readonly alertTicker: Locator;

  constructor(page: Page) {
    this.page = page;
    this.kpiCards = page.locator('[data-testid="kpi-card"]');
    this.duckCurveChart = page.locator('[data-testid="duck-curve-chart"]');
    this.assetMap = page.locator('[data-testid="asset-map"]');
    this.alertTicker = page.locator('[data-testid="alert-ticker"]');
  }

  async goto() {
    await this.page.goto("/dashboard");
    await this.page.waitForLoadState("networkidle");
  }

  async waitForKpiCards(expectedCount: number) {
    await expect(this.kpiCards).toHaveCount(expectedCount, {
      timeout: 15_000,
    });
  }

  async getKpiValue(label: string): Promise<string> {
    const card = this.kpiCards.filter({ hasText: label });
    const value = await card.locator('[data-testid="kpi-value"]').textContent();
    return value ?? "";
  }
}
```

```typescript
// frontend/e2e/pages/assets-page.ts
import { type Locator, type Page, expect } from "@playwright/test";

export class AssetsPage {
  readonly page: Page;
  readonly assetTable: Locator;
  readonly assetMap: Locator;
  readonly mapMarkers: Locator;

  constructor(page: Page) {
    this.page = page;
    this.assetTable = page.locator('[data-testid="asset-table"]');
    this.assetMap = page.locator('[data-testid="asset-map"]');
    this.mapMarkers = page.locator('[data-testid="map-marker"]');
  }

  async goto() {
    await this.page.goto("/assets");
    await this.page.waitForLoadState("networkidle");
  }

  async clickAssetRow(name: string) {
    await this.assetTable
      .getByRole("row", { name })
      .getByRole("link")
      .click();
  }

  async clickMapMarker(index: number) {
    await this.mapMarkers.nth(index).click();
  }
}
```

```typescript
// frontend/e2e/pages/carbon-page.ts
import { type Locator, type Page, expect } from "@playwright/test";

export class CarbonPage {
  readonly page: Page;
  readonly creditTable: Locator;
  readonly statusFilter: Locator;
  readonly portfolioSummary: Locator;

  constructor(page: Page) {
    this.page = page;
    this.creditTable = page.locator('[data-testid="credit-table"]');
    this.statusFilter = page.locator('[data-testid="status-filter"]');
    this.portfolioSummary = page.locator('[data-testid="portfolio-summary"]');
  }

  async goto() {
    await this.page.goto("/carbon");
    await this.page.waitForLoadState("networkidle");
  }

  async filterByStatus(status: string) {
    await this.statusFilter.selectOption(status);
    await this.page.waitForResponse(
      (res) => res.url().includes("/carbon/credits") && res.status() === 200,
    );
  }

  async getCreditCount(): Promise<number> {
    return await this.creditTable
      .locator("tbody tr")
      .count();
  }
}
```

```typescript
// frontend/e2e/pages/health-page.ts
import { type Locator, type Page, expect } from "@playwright/test";

export class HealthPage {
  readonly page: Page;
  readonly alertList: Locator;
  readonly acknowledgeButton: Locator;
  readonly confirmedBadge: Locator;

  constructor(page: Page) {
    this.page = page;
    this.alertList = page.locator('[data-testid="alert-list"]');
    this.acknowledgeButton = page.locator(
      '[data-testid="acknowledge-alert"]',
    );
    this.confirmedBadge = page.locator('[data-testid="acknowledged-badge"]');
  }

  async goto() {
    await this.page.goto("/health");
    await this.page.waitForLoadState("networkidle");
  }

  async acknowledgeFirstAlert() {
    await this.acknowledgeButton.first().click();
    await this.page.waitForResponse(
      (res) =>
        res.url().includes("/health/alerts") && res.status() === 200,
    );
  }
}
```

### 3.4 Key User Journeys

```typescript
// frontend/e2e/journeys/dashboard.spec.ts
import { test, expect } from "@playwright/test";
import { DashboardPage } from "../pages/dashboard-page";

test.describe("Dashboard", () => {
  test("loads all 6 KPI cards with correct data", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForKpiCards(6);

    const currentGen = await dashboard.getKpiValue("Current Generation");
    expect(Number(currentGen.replace(/[^0-9.]/g, ""))).toBeGreaterThan(0);

    const totalRevenue = await dashboard.getKpiValue("Total Revenue");
    expect(totalRevenue).toContain("$");
  });

  test("duck curve chart renders with generation and price overlay", async ({
    page,
  }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await expect(dashboard.duckCurveChart).toBeVisible({ timeout: 10_000 });
    const areas = dashboard.duckCurveChart.locator(
      ".recharts-area",
    );
    await expect(areas.first()).toBeVisible();
  });

  test("asset map renders with markers", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await expect(dashboard.assetMap).toBeVisible({ timeout: 10_000 });
  });

  test("alert ticker shows active alerts", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await expect(dashboard.alertTicker).toBeVisible();
  });
});
```

```typescript
// frontend/e2e/journeys/assets.spec.ts
import { test, expect } from "@playwright/test";
import { AssetsPage } from "../pages/assets-page";
import { DashboardPage } from "../pages/dashboard-page";

test.describe("Assets Navigation & Map Interaction", () => {
  test("navigate from dashboard to assets, view map markers, click marker for details", async ({
    page,
  }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // Navigate via sidebar
    await page.getByRole("link", { name: "Assets" }).click();
    await page.waitForURL("**/assets");

    const assets = new AssetsPage(page);
    await expect(assets.assetTable).toBeVisible({ timeout: 10_000 });
    await expect(assets.assetMap).toBeVisible({ timeout: 10_000 });

    // Click a marker and see details
    const markerCount = await assets.mapMarkers.count();
    if (markerCount > 0) {
      await assets.clickMapMarker(0);
      const popup = page.locator('[data-testid="marker-popup"]');
      await expect(popup).toBeVisible({ timeout: 5_000 });
    }
  });

  test("click asset row navigates to detail page", async ({ page }) => {
    const assets = new AssetsPage(page);
    await assets.goto();
    await expect(assets.assetTable).toBeVisible({ timeout: 10_000 });

    const firstRow = assets.assetTable.locator("tbody tr").first();
    const name = await firstRow.locator("td").first().textContent();
    if (name) {
      await assets.clickAssetRow(name);
      await page.waitForURL(`**/assets/**`);
    }
  });
});
```

```typescript
// frontend/e2e/journeys/carbon.spec.ts
import { test, expect } from "@playwright/test";
import { CarbonPage } from "../pages/carbon-page";

test.describe("Carbon Credits", () => {
  test("credits table loads with portfolio summary", async ({ page }) => {
    const carbon = new CarbonPage(page);
    await carbon.goto();
    await expect(carbon.creditTable).toBeVisible({ timeout: 10_000 });
    await expect(carbon.portfolioSummary).toBeVisible();
  });

  test("filter by status updates credit list", async ({ page }) => {
    const carbon = new CarbonPage(page);
    await carbon.goto();
    const initialCount = await carbon.getCreditCount();

    await carbon.filterByStatus("active");
    await carbon.page.waitForTimeout(1_000);
    const filteredCount = await carbon.getCreditCount();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
  });
});
```

```typescript
// frontend/e2e/journeys/health.spec.ts
import { test, expect } from "@playwright/test";
import { HealthPage } from "../pages/health-page";

test.describe("Health Alerts", () => {
  test("alerts list loads with acknowledge functionality", async ({
    page,
  }) => {
    const health = new HealthPage(page);
    await health.goto();
    await expect(health.alertList).toBeVisible({ timeout: 10_000 });

    const alerts = await health.alertList.locator("tbody tr").count();
    if (alerts > 0) {
      await health.acknowledgeFirstAlert();
      await expect(health.confirmedBadge.first()).toBeVisible({
        timeout: 5_000,
      });
    }
  });
});
```

### 3.5 Accessibility Checks with axe-core

```typescript
// frontend/e2e/accessibility/a11y.spec.ts
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Accessibility", () => {
  test("dashboard page has no critical violations", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    expect(results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    )).toEqual([]);
  });

  test("assets page has no critical violations", async ({ page }) => {
    await page.goto("/assets");
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations.filter(
      (v) => v.impact === "critical",
    )).toEqual([]);
  });

  test("carbon page has no critical violations", async ({ page }) => {
    await page.goto("/carbon");
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations.filter(
      (v) => v.impact === "critical",
    )).toEqual([]);
  });

  test("health page has no critical violations", async ({ page }) => {
    await page.goto("/health");
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations.filter(
      (v) => v.impact === "critical",
    )).toEqual([]);
  });
});
```

### 3.6 Visual Regression Testing

```typescript
// frontend/e2e/visual/dashboard-visual.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Dashboard Visual Regression", () => {
  test("dashboard matches baseline screenshot", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2_000); // wait for charts to render

    await expect(page).toHaveScreenshot("dashboard-full.png", {
      fullPage: true,
      maxDiffPixelRatio: 0.02,
    });
  });

  test("duck curve chart matches baseline", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    const chart = page.locator('[data-testid="duck-curve-chart"]');
    await expect(chart).toBeVisible({ timeout: 10_000 });

    await expect(chart).toHaveScreenshot("duck-curve.png", {
      maxDiffPixelRatio: 0.02,
    });
  });
});
```

Visual snapshots are stored in `frontend/e2e/visual/__snapshots__/`. Update baselines with:

```bash
npx playwright test --update-snapshots
```

---

## 4. Component Testing (Vitest)

### 4.1 Vitest Configuration

```typescript
// frontend/vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["src/components/**/*.tsx", "src/lib/**/*.ts", "src/hooks/**/*.ts"],
      exclude: [
        "src/**/*.test.tsx",
        "src/**/*.spec.tsx",
        "src/**/*.stories.tsx",
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 70,
        statements: 80,
      },
    },
    setupFiles: ["./src/__tests__/setup.ts"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

### 4.2 Component Test Patterns

```typescript
// frontend/src/components/ui/__tests__/kpi-card.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { KpiCard } from "../kpi-card";

describe("KpiCard", () => {
  it("renders label and value", () => {
    render(<KpiCard label="Current Generation" value="1,250 kW" />);
    expect(screen.getByText("Current Generation")).toBeInTheDocument();
    expect(screen.getByText("1,250 kW")).toBeInTheDocument();
  });

  it("shows positive trend in green", () => {
    render(
      <KpiCard label="Revenue" value="$5,790" trend={12.5} />,
    );
    const trend = screen.getByText("+12.5%");
    expect(trend).toHaveClass("text-green-600");
  });

  it("shows negative trend in red", () => {
    render(
      <KpiCard label="Revenue" value="$5,790" trend={-3.2} />,
    );
    const trend = screen.getByText("-3.2%");
    expect(trend).toHaveClass("text-red-600");
  });

  it("renders skeleton when loading", () => {
    const { container } = render(
      <KpiCard label="Generation" loading />,
    );
    expect(container.querySelector('[data-testid="skeleton"]')).toBeTruthy();
  });
});
```

```typescript
// frontend/src/components/features/__tests__/generation-chart.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { GenerationChart } from "../generation-chart";

const mockData = [
  { bucket: "2026-07-22T10:00:00Z", avgKw: 1200, peakKw: 1350 },
  { bucket: "2026-07-22T11:00:00Z", avgKw: 1250, peakKw: 1400 },
];

describe("GenerationChart", () => {
  it("renders chart with provided data", () => {
    const { container } = render(
      <GenerationChart data={mockData} />,
    );
    expect(container.querySelector(".recharts-area")).toBeTruthy();
  });

  it("shows loading state when data is undefined", () => {
    render(<GenerationChart data={undefined} isLoading />);
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows empty state when data is empty array", () => {
    render(<GenerationChart data={[]} />);
    expect(screen.getByText("No generation data available")).toBeInTheDocument();
  });
});
```

---

## 5. Test Data Strategy

### 5.1 Database Cleanup

Every test session gets a fresh database. Tables are dropped and recreated at session start:

```python
@pytest.fixture(scope="session")
async def engine():
    from src.models import Base
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

Each test function gets a transaction that is rolled back after completion. No test data leaks between tests.

### 5.2 Deterministic Seeds

Test data is deterministic with a fixed Faker seed:

```python
import factory

factory.Faker._DEFAULT_LOCALE = "en_US"
Faker = factory.Faker  # Re-export for use in factories
```

Set the seed in `conftest.py`:

```python
@pytest.fixture(autouse=True)
def set_faker_seed():
    factory.Faker.override_default_locale("en_US")
    # Each test gets a unique but reproducible seed based on test name
    import random
    random.seed(42)
```

### 5.3 Factory Usage Rules

1. **Never hard-code IDs.** Use `factory.LazyFunction(uuid4)` for every ID field.
2. **Use `factory.build()`** to create dicts for request payloads (not DB inserts).
3. **Use `factory.create()`** (or an async equivalent) only when the object must exist in the DB.
4. **Overrides at call site** for test-specific values:

```python
def test_asset_with_specific_capacity(authenticated_client):
    payload = AssetFactory.build(capacity_kw=2500.0, asset_type="wind_turbine")
    # Use payload in API call
```

5. **Sequence-based fields** for uniqueness:

```python
code = factory.Sequence(lambda n: f"INV-{n:03d}")
name = factory.Sequence(lambda n: f"Inverter #{n}")
```

### 5.4 Known-Reference Data

For integration tests that need predictable data:

```python
# tests/conftest.py
from uuid import UUID

KNOWN_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
KNOWN_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
KNOWN_ASSET_ID = UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
async def seed_reference_data(db_session):
    """Insert minimal known data that tests reference by ID."""
    from src.models.organization import Organization
    from src.models.user import User
    from src.models.asset import Asset

    org = Organization(id=KNOWN_ORG_ID, name="Test Org", slug="test-org")
    db_session.add(org)
    user = User(
        id=KNOWN_USER_ID,
        organization_id=KNOWN_ORG_ID,
        email="test@urja.io",
        password_hash="<hash>",
        display_name="Test User",
        role="admin",
    )
    db_session.add(user)
    asset = Asset(
        id=KNOWN_ASSET_ID,
        organization_id=KNOWN_ORG_ID,
        site_id=KNOWN_SITE_ID,
        name="Reference Inverter",
        code="REF-001",
        asset_type="inverter",
        capacity_kw=1500.0,
    )
    db_session.add(asset)
    await db_session.commit()
```

---

## 6. CI Integration

### 6.1 CI Test Stages

Refer to [CI-CD.md](CI-CD.md) for the full pipeline. The test-specific jobs are:

| Job | Split Strategy | Services Required | Timeout |
|-----|---------------|-------------------|---------|
| `backend-test` (routers) | Directory split | PostgreSQL, Redis | 10 min |
| `backend-test` (services) | Directory split | None (mocked) | 5 min |
| `backend-test` (tasks) | Directory split | PostgreSQL, Redis | 10 min |
| `backend-test` (integration) | Directory split | PostgreSQL (TimescaleDB), Redis | 15 min |
| `e2e-test` (Playwright) | Shard 1-4 | API, Frontend, PostgreSQL, Redis | 20 min |
| `coverage-report` | Merge all splits | None | 2 min |

### 6.2 Parallel Test Execution

**Backend**: Tests split by directory across 4 parallel runners. Each runner uses `pytest-xdist -n auto`.

```bash
# CI runs these in parallel
pytest tests/routers --cov=src -n auto -v
pytest tests/services --cov=src -n auto -v
pytest tests/tasks --cov=src -n auto -v
pytest tests/integration --cov=src -n auto -v
```

**Frontend**: Playwright shards across 4 parallel runners.

```bash
npx playwright test --shard=1/4
npx playwright test --shard=2/4
npx playwright test --shard=3/4
npx playwright test --shard=4/4
```

### 6.3 Service Containers in CI

```yaml
# .github/workflows/ci.yml (excerpt)
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_DB: urja_test
      POSTGRES_USER: urja
      POSTGRES_PASSWORD: urja_test_pass
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 5s
      --health-timeout 5s
      --health-retries 10

  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 5s
      --health-timeout 5s
      --health-retries 10
```

**TimescaleDB in CI**: CI uses standard PostgreSQL 16. TimescaleDB-specific tests are skipped with `@pytest.mark.skipif`. See [CI-CD.md](CI-CD.md) for details.

### 6.4 Failure Artifacts

On test failure, CI uploads:

- **Playwright traces**: Full action replay in Trace Viewer
- **Screenshots**: Page state at failure moment
- **Videos**: Screen recording leading to failure (first retry only)
- **Console logs**: All `console.log`, `console.error`, and network logs
- **Coverage reports**: XML reports for merged analysis

```yaml
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report-shard-${{ matrix.shard }}
    path: frontend/playwright-report/
    retention-days: 7
```

### 6.5 Coverage Gate

```yaml
# Coverage must be >= 90%
coverage-report:
  needs: [backend-test]
  steps:
    - run: |
        coverage combine coverage-*.xml
        coverage report --fail-under=90
```

If coverage drops below 90%, the CI pipeline fails. Coverage is measured on the `src/` directory only (excluding `alembic/`, `config.py`, `main.py`).

---

## 7. Flake Management

### 7.1 Retry Policy

| Layer | Retries | When |
|-------|---------|------|
| Unit tests | 0 | Never retry — a flaky unit test is a bug |
| Integration tests | 1 | Only if the failure is related to async timing |
| E2E tests | 2 | Network, rendering, and async data races |

Playwright config:
```typescript
retries: process.env.CI ? 2 : 0,
```

pytest retry (integration only):
```python
# pytest.ini
addopts = """
    --reruns 1
    --reruns-delay 2
    --only-rerun "timeout|connection refused"
"""
```

### 7.2 Quarantine Workflow

When a test flakes 3+ times in CI:

1. Move the test to `tests/quarantine/` (backend) or `e2e/quarantine/` (frontend).
2. Create a GitHub issue with the `flaky-test` label.
3. Investigate root cause within 3 business days.
4. Fix and move test back to its original location.
5. Delete the quarantine directory entry.

### 7.3 Common Flake Causes & Fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `page.waitForSelector` timeout | Element not rendered yet | Use `waitForLoadState("networkidle")` first |
| Test passes locally but fails in CI | Race condition with async data | Add explicit `waitForResponse` for the API call |
| Intermittent 5xx from API | Test DB not fully migrated | Ensure Alembic migrations run before tests |
| Visual diff fails by 1px | Font rendering differences | Use `maxDiffPixelRatio: 0.02` |
| Test depends on test order | Shared mutable state | Ensure each test creates its own data |
| `NOT NULL constraint violation` | Factory missing required field | Add missing field to factory |

---

## 8. Testing Commands Reference

### 8.1 Backend Tests

```bash
# Run all backend tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/routers/test_assets.py -v

# Run specific test class
pytest tests/routers/test_assets.py::TestListAssets -v

# Run specific test
pytest tests/routers/test_assets.py::TestListAssets::test_returns_paginated_results -v

# Run with verbose output and fail fast
pytest -x -v

# Run with parallel execution (4 workers)
pytest -n 4

# Run slow tests only
pytest -m slow

# Run all tests except slow
pytest -m "not slow"

# Run TimescaleDB-specific tests
pytest -m timescaledb

# Run integration tests only
pytest -m integration

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Debug a test with full traceback
pytest --tb=long -v --log-cli-level=DEBUG tests/routers/test_assets.py

# Re-run last failed tests
pytest --lf
```

### 8.2 Frontend Tests

```bash
# Run all E2E tests
npx playwright test

# Run in UI mode (interactive debugger)
npx playwright test --ui

# Run specific E2E test file
npx playwright test e2e/journeys/dashboard.spec.ts

# Run tests matching a pattern
npx playwright test --grep "dashboard"

# Run with visible browser (headed mode)
npx playwright test --headed

# Run single browser only
npx playwright test --project=chromium

# Run specific shard
npx playwright test --shard=1/4

# Debug a specific test
npx playwright test --debug e2e/journeys/assets.spec.ts

# Update visual snapshots
npx playwright test --update-snapshots

# Open last HTML report
npx playwright show-report

# Run component tests
npm run test

# Run component tests with coverage
npm run test -- --coverage

# Run component tests in watch mode
npm run test -- --watch
```

### 8.3 Test Data Commands

```bash
# Seed test database with reference data (for manual testing)
uv run python scripts/seed_test_data.py

# Reset test database (drop all tables, re-run migrations)
uv run alembic downgrade base && uv run alembic upgrade head

# Generate factories coverage report (checks every model has a factory)
uv run python scripts/check_factory_coverage.py
```

### 8.4 CI Commands (local simulation)

```bash
# Simulate CI backend test split
pytest tests/routers --cov=src --cov-report=xml:coverage-routers.xml -v
pytest tests/services --cov=src --cov-report=xml:coverage-services.xml -v
pytest tests/tasks --cov=src --cov-report=xml:coverage-tasks.xml -v
pytest tests/integration --cov=src --cov-report=xml:coverage-integration.xml -v

# Merge coverage (requires `pip install coverage`)
coverage combine coverage-*.xml
coverage report --fail-under=90

# Simulate CI E2E with shard 1
npx playwright test --shard=1/4 --project=chromium
```

---

## 9. Testing Checklist (for PRs)

### Backend

- [ ] New endpoints have API tests covering happy path + all error codes (4xx, 5xx)
- [ ] New endpoints have auth failure tests (401 without token, 403 with wrong role)
- [ ] New endpoints test pagination (empty, single page, multi-page with cursor)
- [ ] New services have unit tests with mocked I/O
- [ ] Unit tests cover edge cases (empty inputs, boundary values, null inputs)
- [ ] New database queries are tested (raw SQL or repository pattern)
- [ ] Existing tests still pass (`pytest` — zero failures)
- [ ] Coverage >= 90% for new code (check with `--cov`)
- [ ] No hard sleeps in tests — use `await asyncio.wait_for()` or explicit waits
- [ ] Test names follow `test_{feature}_{scenario}` convention
- [ ] Factory exists for any new SQLAlchemy model
- [ ] Factory overrides are used instead of hard-coded values

### Frontend

- [ ] New pages have E2E coverage for the primary user journey
- [ ] New components have Vitest tests for render, loading, error, and empty states
- [ ] E2E tests use Page Object Model, not raw locators
- [ ] No test logs in through the UI — auth is done via API setup
- [ ] Visual regression snapshots are added for new chart/map components
- [ ] axe-core accessibility check passes for new pages
- [ ] All tests pass 3 consecutive runs locally (`npx playwright test --repeat-each=3`)

### General

- [ ] No test depends on another test's data (test order independence verified)
- [ ] All tests run and pass in CI (push to a feature branch to verify)
- [ ] PR description includes testing notes: what was tested manually, what was automated
- [ ] No `.only` or `.skip` left in test files (checked with `grep -r "\.only\|\.skip" tests/ e2e/`)
- [ ] No `console.log` debugging artifacts in test files
- [ ] No secrets, tokens, or credentials in test files or recorded in Playwright traces

---

## 10. Appendix: File Reference

### 10.1 Test Configuration Files

| File | Purpose |
|------|---------|
| `backend/pyproject.toml` | pytest, coverage, and mypy configuration |
| `backend/tests/conftest.py` | Global fixtures: engine, db_session, client, auth |
| `backend/tests/factories/*.py` | factory_boy factories for all models |
| `frontend/playwright.config.ts` | Playwright configuration, projects, retries |
| `frontend/vitest.config.ts` | Vitest configuration for component tests |
| `frontend/e2e/auth.setup.ts` | API-based auth setup for Playwright |
| `frontend/e2e/pages/*.ts` | Page Object Model classes |
| `.github/workflows/ci.yml` | CI pipeline with test jobs |

### 10.2 Test Directory Summary

```
backend/tests/                          # Backend test suite
├── conftest.py                         # Global fixtures
├── factories/                          # factory_boy factories
├── routers/                            # API endpoint tests
├── services/                           # Service layer unit tests
├── tasks/                              # ARQ task tests
├── integration/                        # Cross-cutting integration tests
└── quarantine/                         # Flaky tests under investigation

frontend/
├── e2e/                                # Playwright E2E tests
│   ├── auth.setup.ts                   # Auth setup for test sessions
│   ├── pages/                          # Page Object Model
│   ├── journeys/                       # User journey tests
│   ├── visual/                         # Visual regression tests
│   └── accessibility/                  # axe-core a11y tests
├── src/
│   └── components/
│       ├── ui/__tests__/               # UI component tests (Vitest)
│       └── features/__tests__/         # Feature component tests (Vitest)
```

### 10.3 Related Documents

- [CI-CD.md](CI-CD.md) — CI/CD pipeline with test stages, parallelization, and caching
- [GUIDELINES.md](GUIDELINES.md) — Coding standards with testing requirements
- [ARCHITECTURE.md](../technical/ARCHITECTURE.md) — System architecture (C4 model)
- [API-SPEC.md](../technical/API-SPEC.md) — Complete API reference for endpoint test coverage
- [DATABASE.md](../technical/DATABASE.md) — Database schema and TimescaleDB configuration

---

## Quick Start for New Contributors

1. Install test dependencies:
   ```bash
   cd backend && uv sync --group dev
   cd frontend && npm ci && npx playwright install --with-deps
   ```

2. Start test infrastructure:
   ```bash
   docker compose up -d db redis
   ```

3. Run the full test suite:
   ```bash
   cd backend && pytest --cov=src --cov-report=term-missing
   cd frontend && npm test && npx playwright test
   ```

4. Open coverage reports:
   ```bash
   open backend/htmlcov/index.html
   npx playwright show-report frontend/playwright-report
   ```

5. Read this entire document before writing your first test.
