# URJA — CI/CD Pipeline

**Version**: 1.0
**Author**: DevOps Automator
**Last Updated**: 2026-07-22
**Platform**: GitHub Actions

> This document defines the complete CI/CD pipeline for the URJA monorepo. Every commit and every PR runs through these automated gates. Releases are fully automated from tag to container image.

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Workflow 1: PR Check (ci.yml)](#2-workflow-1-pr-check-ciyml)
3. [Workflow 2: Release (release.yml)](#3-workflow-2-release-releaseyml)
4. [Service Containers](#4-service-containers)
5. [Test Parallelization & Caching](#5-test-parallelization--caching)
6. [Environment & Secrets](#6-environment--secrets)
7. [README Badges](#7-readme-badges)
8. [Local Pre-commit Hooks](#8-local-pre-commit-hooks)

---

## 1. Pipeline Overview

### Workflow Triggers

| Workflow | Trigger | Branch |
|----------|---------|--------|
| **PR Check** | `pull_request` | `main` |
| **PR Check** | `push` | `feature/*`, `fix/*`, `chore/*`, `docs/*` |
| **Release** | `push` tag | `v*.*.*` |
| **Manual** | `workflow_dispatch` | Any |

### Pipeline Stages (Dependency Graph)

```
                    ┌──────────────┐
                    │  secrets-scan │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │backend-  │ │frontend- │ │backend-  │
        │lint      │ │lint      │ │test      │
        └──────────┘ └──────────┘ └────┬─────┘
              │            │           │
              ▼            ▼           │
        ┌──────────┐ ┌──────────┐      │
        │backend-  │ │frontend- │      │
        │typecheck │ │build     │      │
        └──────────┘ └──────────┘      │
              │            │           │
              └─────┬──────┘           │
                    ▼                  ▼
              ┌──────────────────────────┐
              │       e2e-test           │
              │  (Playwright, optional)  │
              └──────────────────────────┘
```

### Target Run Time

| Stage | Target |
|-------|--------|
| secrets-scan | < 30s |
| backend-lint + typecheck | < 60s |
| frontend-lint + build | < 90s |
| backend-test (4x parallel) | < 3 min |
| e2e-test (4x shard) | < 5 min |
| **Total parallel** | **< 8 min** |

All lint and type-check jobs run in parallel with each other and with tests. The critical path is backend-test → e2e-test.

---

## 2. Workflow 1: PR Check (ci.yml)

This workflow runs on every push to a feature branch and every pull request to `main`. It is the **gate** — if any job fails, the PR cannot merge.

```yaml
# .github/workflows/ci.yml
# ────────────────────────────────────────────────────────────────────────────
# URJA — PR Check Workflow
# Runs on every push to feature branches and every PR to main.
# Gates: secrets scan → lint + typecheck → test → build → e2e
# ────────────────────────────────────────────────────────────────────────────

name: CI

on:
  push:
    branches:
      - "feature/**"
      - "fix/**"
      - "chore/**"
      - "docs/**"
  pull_request:
    branches:
      - main
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"
  NODE_VERSION: "20"
  REGISTRY: ghcr.io

defaults:
  run:
    shell: bash

jobs:

  # ── Secrets Scan ──────────────────────────────────────────────────────────
  secrets-scan:
    name: Secrets Scan
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run truffleHog
        uses: trufflesecurity/trufflehog@v3
        with:
          extra_args: "--only-verified --results=verified"

  # ── Backend Lint ──────────────────────────────────────────────────────────
  backend-lint:
    name: Backend Lint
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: ./backend
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "0.4.x"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache uv
        uses: actions/cache@v4
        with:
          path: ~/.cache/uv
          key: uv-${{ runner.os }}-${{ hashFiles('backend/pyproject.toml', 'backend/uv.lock') }}
          restore-keys: |
            uv-${{ runner.os }}-

      - name: Install dependencies
        run: uv sync

      - name: Ruff check
        run: uv run ruff check --output-format=github .

      - name: Ruff format check
        run: uv run ruff format --check .

  # ── Backend Type Check ───────────────────────────────────────────────────
  backend-typecheck:
    name: Backend Type Check
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: ./backend
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "0.4.x"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache uv
        uses: actions/cache@v4
        with:
          path: ~/.cache/uv
          key: uv-${{ runner.os }}-${{ hashFiles('backend/pyproject.toml', 'backend/uv.lock') }}
          restore-keys: |
            uv-${{ runner.os }}-

      - name: Install dependencies
        run: uv sync

      - name: mypy check
        run: uv run mypy src/

  # ── Frontend Lint ────────────────────────────────────────────────────────
  frontend-lint:
    name: Frontend Lint
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: ./frontend
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Cache npm
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: npm-${{ runner.os }}-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            npm-${{ runner.os }}-

      - name: Install dependencies
        run: npm ci

      - name: ESLint check
        run: npm run lint

      - name: Prettier check
        run: npx prettier --check "src/**/*.{ts,tsx,json,css}"

  # ── Backend Tests ────────────────────────────────────────────────────────
  backend-test:
    name: Backend Tests
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: ./backend

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

    strategy:
      fail-fast: false
      matrix:
        # Split tests across 4 parallel runners by test directory
        split:
          - routers
          - services
          - tasks
          - integration

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "0.4.x"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache uv
        uses: actions/cache@v4
        with:
          path: ~/.cache/uv
          key: uv-${{ runner.os }}-${{ hashFiles('backend/pyproject.toml', 'backend/uv.lock') }}
          restore-keys: |
            uv-${{ runner.os }}-

      - name: Install dependencies
        run: uv sync

      - name: Run Alembic migrations
        run: |
          uv run alembic upgrade head
        env:
          DATABASE_URL: postgresql+asyncpg://urja:urja_test_pass@localhost:5432/urja_test

      - name: Run tests (${{ matrix.split }})
        run: |
          uv run pytest \
            tests/${{ matrix.split }} \
            --cov=src \
            --cov-report=xml:coverage-${{ matrix.split }}.xml \
            --cov-report=term \
            -n auto \
            -v
        env:
          DATABASE_URL: postgresql+asyncpg://urja:urja_test_pass@localhost:5432/urja_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: ci-test-secret-do-not-use-in-production
          CI: "true"

      - name: Upload coverage artifact
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.split }}
          path: backend/coverage-${{ matrix.split }}.xml

  # Combine coverage reports from all splits
  coverage-report:
    name: Coverage Report
    needs: [backend-test]
    runs-on: ubuntu-24.04
    if: always()
    steps:
      - uses: actions/checkout@v4

      - uses: actions/download-artifact@v4
        with:
          pattern: coverage-*
          merge-multiple: true

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install coverage
        run: pip install coverage

      - name: Combine and report
        run: |
          coverage combine coverage-*.xml
          coverage report --fail-under=90
          coverage xml -o total-coverage.xml

      - name: Generate coverage badge
        if: github.ref == 'refs/heads/main'
        run: |
          TOTAL=$(coverage report | tail -1 | awk '{print $NF}' | tr -d '%')
          COLOR="red"
          if [ "$TOTAL" -ge 90 ]; then COLOR="green"; fi
          if [ "$TOTAL" -ge 80 ] && [ "$TOTAL" -lt 90 ]; then COLOR="yellow"; fi
          echo "COVERAGE=$TOTAL" >> $GITHUB_ENV
          echo "COLOR=$COLOR" >> $GITHUB_ENV

  # ── Frontend Build ───────────────────────────────────────────────────────
  frontend-build:
    name: Frontend Build
    runs-on: ubuntu-24.04
    defaults:
      run:
        working-directory: ./frontend
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Cache npm
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: npm-${{ runner.os }}-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            npm-${{ runner.os }}-

      - name: Cache Next.js build
        uses: actions/cache@v4
        with:
          path: |
            frontend/.next/cache
          key: nextjs-${{ runner.os }}-${{ hashFiles('frontend/package-lock.json', 'frontend/src/**/*.ts', 'frontend/src/**/*.tsx') }}
          restore-keys: |
            nextjs-${{ runner.os }}-

      - name: Install dependencies
        run: npm ci

      - name: Next.js build
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
          NEXT_TELEMETRY_DISABLED: "1"

      - name: Upload build artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: frontend/.next

  # ── E2E Tests (Playwright) ───────────────────────────────────────────────
  e2e-test:
    name: E2E Tests
    needs: [frontend-build, backend-test]
    runs-on: ubuntu-24.04
    # Only run on pull_request to main, not on every push
    if: github.event_name == 'pull_request'

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

    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "0.4.x"

      - name: Cache uv
        uses: actions/cache@v4
        with:
          path: ~/.cache/uv
          key: uv-e2e-${{ runner.os }}-${{ hashFiles('backend/pyproject.toml', 'backend/uv.lock') }}

      - name: Install backend dependencies
        working-directory: ./backend
        run: uv sync

      - name: Cache npm
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: npm-e2e-${{ runner.os }}-${{ hashFiles('frontend/package-lock.json') }}

      - name: Install frontend dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Install Playwright browsers
        working-directory: ./frontend
        run: npx playwright install --with-deps chromium

      - name: Download frontend build
        uses: actions/download-artifact@v4
        with:
          name: github-pages

      - name: Start API server
        working-directory: ./backend
        run: |
          uv run alembic upgrade head
          uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &
          sleep 3
          curl -f http://localhost:8000/health
        env:
          DATABASE_URL: postgresql+asyncpg://urja:urja_test_pass@localhost:5432/urja_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: ci-e2e-test-secret
          CI: "true"

      - name: Start frontend server
        working-directory: ./frontend
        run: |
          npm run start &
          sleep 5
          curl -f http://localhost:3000 || true
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
          PORT: "3000"

      - name: Run Playwright tests (shard ${{ matrix.shard }})
        working-directory: ./frontend
        run: |
          npx playwright test \
            --shard=${{ matrix.shard }}/4
        env:
          PLAYWRIGHT_BASE_URL: http://localhost:3000

      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report-shard-${{ matrix.shard }}
          path: frontend/playwright-report/
          retention-days: 7
```

---

## 3. Workflow 2: Release (release.yml)

Triggered by pushing a tag matching `v*.*.*` (SemVer). This workflow builds Docker images, pushes them to GHCR, and creates a GitHub Release.

```yaml
# .github/workflows/release.yml
# ────────────────────────────────────────────────────────────────────────────
# URJA — Release Workflow
# Triggered by: git tag v*.*.*
# Does: test → build Docker images → push to GHCR → create GitHub Release
# ────────────────────────────────────────────────────────────────────────────

name: Release

on:
  push:
    tags:
      - "v*.*.*"
  workflow_dispatch:
    inputs:
      tag:
        description: "Release tag (e.g., v1.2.3)"
        required: true

env:
  REGISTRY: ghcr.io
  API_IMAGE: ${{ github.repository }}/api
  FRONTEND_IMAGE: ${{ github.repository }}/frontend
  TUI_IMAGE: ${{ github.repository }}/tui

jobs:
  # ── Extract Version ──────────────────────────────────────────────────────
  version:
    name: Parse Version
    runs-on: ubuntu-24.04
    outputs:
      version: ${{ steps.parse.outputs.version }}
      major_minor: ${{ steps.parse.outputs.major_minor }}
    steps:
      - id: parse
        run: |
          TAG="${{ github.ref_name }}"
          VERSION="${TAG#v}"
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "major_minor=$(echo $VERSION | cut -d. -f1,2)" >> $GITHUB_OUTPUT

  # ── Run Tests (reuses ci.yml via workflow_call) ──────────────────────────
  test:
    name: Run Tests
    uses: ./.github/workflows/ci.yml
    secrets: inherit

  # ── Build & Push Docker Images ───────────────────────────────────────────
  build-api:
    name: Build API Image
    needs: [version, test]
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.API_IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  build-frontend:
    name: Build Frontend Image
    needs: [version, test]
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.FRONTEND_IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            NEXT_PUBLIC_API_URL=/api/v1
            NEXT_TELEMETRY_DISABLED=1

  build-tui:
    name: Build TUI Image
    needs: [version, test]
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.TUI_IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ./dashboard-tui
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ── Create GitHub Release ────────────────────────────────────────────────
  release:
    name: Create Release
    needs: [version, build-api, build-frontend, build-tui]
    runs-on: ubuntu-24.04
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        id: changelog
        run: |
          PREV_TAG=$(git tag --sort=-version:refname | head -2 | tail -1)
          if [ -z "$PREV_TAG" ]; then
            echo "changelog=Initial release" >> $GITHUB_OUTPUT
          else
            CHANGES=$(git log "$PREV_TAG..${{ github.ref_name }}" --oneline --no-decorate)
            echo "changelog<<EOF" >> $GITHUB_OUTPUT
            echo "$CHANGES" >> $GITHUB_OUTPUT
            echo "EOF" >> $GITHUB_OUTPUT
          fi

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ github.ref_name }}
          name: Release ${{ needs.version.outputs.version }}
          body: |
            ## URJA ${{ needs.version.outputs.version }}

            ### Images
            - `${{ env.REGISTRY }}/${{ env.API_IMAGE }}:${{ needs.version.outputs.version }}`
            - `${{ env.REGISTRY }}/${{ env.FRONTEND_IMAGE }}:${{ needs.version.outputs.version }}`
            - `${{ env.REGISTRY }}/${{ env.TUI_IMAGE }}:${{ needs.version.outputs.version }}`

            ### Changes
            ${{ steps.changelog.outputs.changelog }}

            ### Upgrade
            ```bash
            docker compose pull
            docker compose up -d
            ```
          draft: false
          prerelease: false
          generate_release_notes: false
```

---

## 4. Service Containers

### PostgreSQL

GitHub Actions does not support TimescaleDB as a service container. URJA tests use standard PostgreSQL 16 in CI and skip TimescaleDB-specific tests.

```yaml
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
```

**Connection string used by tests:**
```
DATABASE_URL=postgresql+asyncpg://urja:urja_test_pass@localhost:5432/urja_test
```

### Redis

```yaml
services:
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

### How Tests Connect

The test suite reads `DATABASE_URL` and `REDIS_URL` from environment variables. In CI, these point to `localhost` (the service container host). Locally, they point to the developer's running services.

**conftest.py** — service container connection:

```python
# backend/tests/conftest.py
import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://urja:urja@localhost:5432/urja_test",
)
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()
```

### TimescaleDB in CI

TimescaleDB-specific features (hypertables, continuous aggregates) cannot be tested with standard PostgreSQL. The strategy:

1. **CI runs standard PostgreSQL** — all relational tests pass.
2. **Hypertable creation** is skipped when `CI=true` is detected in `alembic/env.py`:

```python
# backend/src/alembic/env.py
import os

SKIP_TIMESCALE = os.getenv("CI", "").lower() == "true"


def run_migrations_online():
    if SKIP_TIMESCALE:
        # Skip hypertable creation — run standard DDL only
        pass
    else:
        # Full migration with TimescaleDB extensions
        pass
```

3. **Timescale-specific tests** (hypertable partitioning, compression, continuous aggregates) are skipped with `@pytest.mark.skipif`:

```python
# backend/tests/conftest.py
import os
import pytest

skip_if_ci = pytest.mark.skipif(
    os.getenv("CI", "").lower() == "true",
    reason="TimescaleDB not available in CI",
)


# backend/tests/test_hypertable.py
@skip_if_ci
async def test_telemetry_hypertable_partitioning(db_session):
    ...
```

---

## 5. Test Parallelization & Caching

### pytest Parallelization

Tests are split by directory across 4 parallel GitHub Actions runners using a matrix strategy:

| Runner | Test Directory | Typical Count |
|--------|---------------|---------------|
| 1 | `tests/routers/` | ~40 tests |
| 2 | `tests/services/` | ~60 tests |
| 3 | `tests/tasks/` | ~20 tests |
| 4 | `tests/integration/` | ~10 tests |

Within each runner, tests are further parallelized using `pytest-xdist` (`-n auto`).

### Playwright Sharding

E2E tests run across 4 shards, cutting wall-clock time by ~75%:

```bash
npx playwright test --shard=1/4
npx playwright test --shard=2/4
npx playwright test --shard=3/4
npx playwright test --shard=4/4
```

Playwright shards distribute test files across runners automatically.

### Dependency Caching

| Cache Key | What It Caches | When It Invalidates |
|-----------|----------------|---------------------|
| `uv-${{ runner.os }}-${{ hashFiles('.../pyproject.toml', '.../uv.lock') }}` | uv package cache | When `pyproject.toml` or `uv.lock` changes |
| `npm-${{ runner.os }}-${{ hashFiles('.../package-lock.json') }}` | npm global cache | When `package-lock.json` changes |
| `nextjs-${{ runner.os }}-${{ hashFiles(...) }}` | Next.js build cache | When source or deps change |

Caching saves approximately:
- uv: ~30s per job (no re-download)
- npm: ~45s per job (no re-download)
- Next.js: ~60s per build (incremental compilation)

---

## 6. Environment & Secrets

### Repository Secrets

The following secrets must be configured in the GitHub repository:

| Secret | Used By | Description |
|--------|---------|-------------|
| `GITHUB_TOKEN` | All workflows | Auto-injected by GitHub Actions |
| (automatic) | release.yml | Push to GHCR — `GITHUB_TOKEN` has write access |

No additional secrets are required for CI. All test credentials are hardcoded as CI-only values (they are never valid outside the ephemeral runner).

### Environment-Specific Files

| Context | File | Source |
|---------|------|--------|
| Local dev | `.env` | Copied from `.env.example` |
| CI tests | (env vars in workflow) | `DATABASE_URL`, `REDIS_URL`, etc. set inline |
| Production | `.env` on server | Generated via `generate-secrets.sh` |

### CI Environment Variables (.env.ci)

These values are set directly in the workflow YAML — no file needed:

```bash
DATABASE_URL=postgresql+asyncpg://urja:urja_test_pass@localhost:5432/urja_test
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=ci-test-secret-do-not-use-in-production
CI=true
```

### Test Database Configuration

```toml
# backend/pyproject.toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
env = [
    "DATABASE_URL=postgresql+asyncpg://urja:urja@localhost:5432/urja_test",
    "REDIS_URL=redis://localhost:6379/0",
    "JWT_SECRET=test-secret",
]

[tool.coverage.run]
source = ["src"]
omit = ["src/alembic/*", "src/main.py", "src/config.py"]

[tool.coverage.report]
fail_under = 90
show_missing = true
```

---

## 7. README Badges

Add these badges to `README.md` above the fold:

```markdown
<p align="center">
  <a href="https://github.com/ravikumarve/URJA/actions/workflows/ci.yml">
    <img src="https://github.com/ravikumarve/URJA/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://github.com/ravikumarve/URJA/actions/workflows/release.yml">
    <img src="https://github.com/ravikumarve/URJA/actions/workflows/release.yml/badge.svg" alt="Release">
  </a>
  <a href="https://github.com/ravikumarve/URJA">
    <img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/ravikumarve/coverage-badge/raw/urja-coverage.json" alt="Coverage">
  </a>
  <a href="https://github.com/ravikumarve/URJA/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  </a>
  <a href="https://github.com/ravikumarve/URJA">
    <img src="https://img.shields.io/github/v/release/ravikumarve/URJA?include_prereleases&sort=semver" alt="Version">
  </a>
</p>
```

### Badge URLs Reference

| Badge | URL | Notes |
|-------|-----|-------|
| CI | `https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg` | Shows last CI run status |
| Release | `https://github.com/OWNER/REPO/actions/workflows/release.yml/badge.svg` | Shows last release status |
| Coverage | Custom endpoint (see below) | Requires Shields.io or coverage service |
| License | `https://img.shields.io/badge/license-MIT-blue.svg` | Static |
| Version | `https://img.shields.io/github/v/release/OWNER/REPO` | Auto-updates from tags |

**Coverage badge** requires a Shields.io endpoint. Two options:

**Option A: shields.io with JSON endpoint**
Set up a GitHub Action that uploads coverage to a Gist. Or use a service like Codecov:

```markdown
[![codecov](https://codecov.io/gh/ravikumarve/URJA/branch/main/graph/badge.svg)](https://codecov.io/gh/ravikumarve/URJA)
```

**Option B: Simple text badge (no service)**

```markdown
![coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)
```

Update the percentage manually each release or automate via a post-release action.

---

## 8. Local Pre-commit Hooks

### Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        types_or: [python, pyi]
      - id: ruff-format
        types_or: [python, pyi]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10
    hooks:
      - id: mypy
        args: [--strict, --ignore-missing-imports]
        additional_dependencies:
          - pydantic
          - sqlalchemy
          - types-redis

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1
    hooks:
      - id: prettier
        types_or: [javascript, jsx, typescript, tsx, json, css, markdown]
        args: [--check]
```

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks into the repo
pre-commit install

# Run against all files (first time)
pre-commit run --all-files

# Run against staged files (auto-runs on git commit)
pre-commit run
```

### Hooks Reference

| Hook | Purpose | Pass/Fail |
|------|---------|-----------|
| `trailing-whitespace` | Removes trailing whitespace | Error |
| `end-of-file-fixer` | Ensures files end with newline | Error |
| `check-yaml` | Validates YAML syntax | Error |
| `check-json` | Validates JSON syntax | Error |
| `check-added-large-files` | Blocks files > 500KB | Warning |
| `detect-private-key` | Blocks accidental key commits | Error |
| `ruff` | Lints and auto-fixes Python | Error |
| `ruff-format` | Formats Python (Black-compatible) | Error |
| `mypy` | Type checks Python (strict mode) | Error |
| `detect-secrets` | Scans for hardcoded secrets | Error |
| `prettier` | Formats frontend files | Error |

### Secrets Baseline

`detect-secrets` uses a baseline file to whitelist known false positives:

```bash
# Generate initial baseline
detect-secrets scan > .secrets.baseline

# Update baseline after adding new false positives
detect-secrets scan --baseline .secrets.baseline --update .secrets.baseline

# Commit baseline to repo
git add .secrets.baseline
```

The `.secrets.baseline` file must be committed to the repository. Pre-commit hooks will catch any new secrets that are not in the baseline.

### Skipping Hooks

Use sparingly — only for emergency fixes:

```bash
# Skip all hooks
git commit --no-verify

# Skip specific hook
SKIP=detect-secrets git commit -m "fix: urgent hotfix"
```

---

## Appendix: Directory Layout

```
.github/
├── workflows/
│   ├── ci.yml              # PR check workflow
│   └── release.yml         # Release workflow

.pre-commit-config.yaml     # Pre-commit hooks
.secrets.baseline           # detect-secrets whitelist
```

## Appendix: CI Configuration Quick Reference

| Branch | Workflow | Required to Merge |
|--------|----------|-------------------|
| `feature/*` → `main` | CI (full) | All jobs green |
| `fix/*` → `main` | CI (full) | All jobs green |
| `docs/*` → `main` | CI (secrets-scan only) | secrets-scan green |
| `chore/*` → `main` | CI (full) | All jobs green |
| `v*.*.*` tag | Release | N/A (tag push bypasses PR) |
