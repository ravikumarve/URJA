# URJA — API Specification

**Version**: 1.0
**Author**: API Platform Engineer
**Last Updated**: 2026-07-22
**Base URL**: `http://localhost:8000/api/v1`
**Protocol**: HTTPS (production), HTTP (local development)
**Content Type**: `application/json`

> This document is the complete API contract for URJA — a RESTful boilerplate for renewable energy asset management. Every endpoint, schema, error code, and auth method is documented here. The API is designed for both human consumption (web dashboard, TUI) and machine consumption (SCADA integrations, external monitoring tools). Auto-generated OpenAPI/Swagger docs are available at `GET /docs` and `GET /redoc` when the API server is running.

---

## Table of Contents

1. [API Overview](#1-api-overview)
2. [Authentication & Authorization](#2-authentication--authorization)
3. [Conventions](#3-conventions)
4. [Rate Limiting](#4-rate-limiting)
5. [Endpoint Reference](#5-endpoint-reference)
   - [5.1 Auth Endpoints](#51-auth-endpoints)
   - [5.2 Organization & Admin](#52-organization--admin)
   - [5.3 Asset Endpoints](#53-asset-endpoints)
   - [5.4 Telemetry Endpoints](#54-telemetry-endpoints)
   - [5.5 Curtailment & Dispatch Endpoints](#55-curtailment--dispatch-endpoints)
   - [5.6 Carbon Endpoints](#56-carbon-endpoints)
   - [5.7 Health Endpoints](#57-health-endpoints)
6. [Common Error Codes](#6-common-error-codes)
7. [Example Workflows](#7-example-workflows)
8. [SDK & Client Generation](#8-sdk--client-generation)

---

## 1. API Overview

### Base URL

| Environment | URL |
|---|---|
| Local development | `http://localhost:8000/api/v1` |
| Docker Compose | `http://api:8000/api/v1` (internal) |
| Production | `https://your-domain.com/api/v1` |

### Versioning Strategy

URJA uses URL-prefix versioning (`/api/v1/`). The current version is `v1`. When breaking changes are introduced, a new version path (`/api/v2/`) is added while `v1` is maintained for a deprecation period.

**Version lifecycle:**
- `v1` — current, actively maintained
- `v2` — not yet released
- Each version has a minimum 6-month deprecation window with clear migration guides

### Content Type

All requests and responses use `application/json`. The API expects `Content-Type: application/json` on all `POST`, `PUT`, and `PATCH` requests. Responses return `Content-Type: application/json`.

### Authentication Methods

| Method | Header | Used By |
|---|---|---|
| JWT Bearer Token | `Authorization: Bearer <token>` | Web dashboard, TUI |
| API Key | `X-API-Key: <key>` | SCADA integrations, external tools |

---

## 2. Authentication & Authorization

### 2.1 JWT Token Flow (Human Users)

```
┌──────────┐       POST /auth/login        ┌──────────┐
│          │  ──────────────────────────►   │          │
│  Client  │       Email + Password         │   API    │
│          │  ◄──────────────────────────   │          │
└──────────┘       Access + Refresh Tokens  └──────────┘
     │                                              │
     │  Authorization: Bearer <access_token>        │
     │  ───────────────────────────────────────►    │
     │  <───────────────────────────────────────    │
     │        200 OK (or 401 if expired)            │
     │                                              │
     │  POST /auth/refresh                          │
     │  Cookie: refresh_token=<token>               │
     │  ───────────────────────────────────────►    │
     │  ◄───────────────────────────────────────    │
     │        New access + refresh tokens            │
```

- **Access token**: JWT signed with HS256, 15-minute TTL. Sent as `Authorization: Bearer <token>`.
- **Refresh token**: JWT signed with HS256, 7-day TTL. Sent as httpOnly, Secure, SameSite=Strict cookie. SHA-256 hash stored in `sessions` table for revocation.
- On refresh, a new refresh token is issued and the old one is revoked (rotation).
- Logout invalidates the refresh token server-side, preventing new access tokens from being issued.

### 2.2 API Key Auth (Machine-to-Machine)

API keys are pre-generated UUID v4 strings with a `urja_` prefix (e.g., `urja_a1b2c3d4e5f6...`). The full key is shown **once** on creation. SHA-256 hash is stored in the database.

```http
GET /api/v1/assets
X-API-Key: urja_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

### 2.3 Token Payload

```json
{
  "sub": "user_abc123",
  "org": "org_xyz789",
  "roles": ["admin"],
  "iat": 1712345678,
  "exp": 1712346578
}
```

### 2.4 RBAC Roles

| Role | Scope | Permissions |
|---|---|---|
| `admin` | Organization-wide | Full CRUD, user management, API keys, dispatch rules, settings |
| `operator` | Organization-wide | View all, acknowledge alerts, export reports, run dispatch optimization |
| `viewer` | Organization-wide | View-only access to all dashboards and exports |

### 2.5 API Key Scopes

| Scope | Allowed Actions |
|---|---|
| `read` | GET endpoints only |
| `write` | GET + POST + PUT endpoints |
| `admin` | All actions including DELETE and API key management |

---

## 3. Conventions

### 3.1 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Request/response fields | `snake_case` | `energy_kwh`, `asset_type` |
| URL paths | `kebab-case` | `/api/v1/curtailment/events` |
| Query parameters | `snake_case` | `?per_page=20&asset_type=inverter` |
| Enum values | `snake_case` | `charge_battery`, `price_above` |
| JSON keys | `snake_case` | `{"health_score": 95.5}` |

### 3.2 Pagination

All list endpoints use cursor-based pagination.

**Request parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | `null` | Opaque cursor from previous response |
| `per_page` | integer | `20` | Items per page (max `100`) |

**Response format:**
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6IjEyMyJ9",
    "has_more": true,
    "total": 156
  }
}
```

To fetch the next page:
```http
GET /api/v1/assets?cursor=eyJpZCI6IjEyMyJ9&per_page=20
```

### 3.3 Standard Response Envelope

**Success response:**
```json
{
  "data": { ... },
  "pagination": { ... },
  "meta": {
    "request_id": "req_a1b2c3d4",
    "timestamp": "2026-07-22T12:00:00Z"
  }
}
```

**Error response (RFC 7807 Problem Details):**
```json
{
  "type": "https://api.urja.dev/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request body contains invalid fields.",
  "instance": "/api/v1/assets",
  "errors": [
    {
      "field": "capacity_kw",
      "message": "Must be greater than 0",
      "code": "greater_than"
    }
  ],
  "meta": {
    "request_id": "req_a1b2c3d4",
    "timestamp": "2026-07-22T12:00:00Z"
  }
}
```

### 3.4 Date & Time Format

- All timestamps use **ISO 8601** with timezone: `2026-07-22T14:30:00Z`
- Date-only fields: `2026-07-22`
- Timezone-aware: always UTC. Clients convert to local timezone.
- Time ranges use `start_date` and `end_date` query parameters (inclusive-exclusive).

### 3.5 Idempotency

`POST` endpoints that create resources support idempotency via the `Idempotency-Key` header. If the same key is sent within 24 hours, the original response is returned without creating a duplicate resource.

```http
POST /api/v1/carbon/issue
Idempotency-Key: idem_abc123def456
Content-Type: application/json

{ ... }
```

### 3.6 Filtering

List endpoints support consistent filtering via query parameters. Common filters:

| Pattern | Example | Description |
|---|---|---|
| Exact match | `?status=active` | Filter by field value |
| Multiple values | `?asset_type=inverter&asset_type=meter` | Match any of |
| Range | `?min_capacity=100&max_capacity=5000` | Numeric range |
| Date range | `?start_date=2026-01-01&end_date=2026-07-01` | Time range |
| Search | `?q=solar+panel` | Full-text search across name/code/description |

---

## 4. Rate Limiting

### 4.1 Rate Limit Tiers

| Tier | Limit | Burst | Applied To |
|---|---|---|---|
| Authenticated (JWT) | 300 req/min | 50 req | Per user |
| API Key (read) | 1,000 req/min | 100 req | Per key |
| API Key (write) | 500 req/min | 50 req | Per key |
| Unauthenticated | 20 req/min | 5 req | Per IP |

### 4.2 Rate Limit Headers

Every response includes rate limit headers:

```http
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 287
X-RateLimit-Reset: 1712346878
Retry-After: 45
```

When rate limit is exceeded:
```json
{
  "type": "https://api.urja.dev/errors/rate-limited",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please wait before retrying.",
  "instance": "/api/v1/telemetry"
}
```

### 4.3 Telemetry Ingestion Specific Limits

Telemetry ingestion has a separate, higher rate limit to accommodate batch data uploads:

| Auth Method | Limit | Burst |
|---|---|---|
| API Key (write/admin) | 10,000 req/min | 500 req |
| JWT (admin only) | 5,000 req/min | 200 req |

---

## 5. Endpoint Reference

### 5.1 Auth Endpoints

---

#### `POST /api/v1/auth/register`

Register a new organization with an admin user.

**Authentication:** None

**Request Body:**
```json
{
  "organization_name": "My Solar Farm",
  "organization_slug": "my-solar-farm",
  "email": "admin@mysolar.com",
  "password": "SecurePass123!",
  "display_name": "Alex Admin",
  "timezone": "America/Los_Angeles",
  "currency": "USD"
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "organization": {
      "id": "org_a1b2c3d4",
      "name": "My Solar Farm",
      "slug": "my-solar-farm",
      "timezone": "America/Los_Angeles",
      "currency": "USD"
    },
    "user": {
      "id": "user_x9y8z7w6",
      "email": "admin@mysolar.com",
      "display_name": "Alex Admin",
      "role": "admin"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

**Error codes:** `409` (email or slug already exists), `422` (validation error)

---

#### `POST /api/v1/auth/login`

Authenticate with email and password. Returns access and refresh tokens.

**Authentication:** None

**Request Body:**
```json
{
  "email": "admin@mysolar.com",
  "password": "SecurePass123!"
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "user": {
      "id": "user_x9y8z7w6",
      "email": "admin@mysolar.com",
      "display_name": "Alex Admin",
      "role": "admin",
      "organization_id": "org_a1b2c3d4"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

**Error codes:** `401` (invalid credentials), `422` (validation error)

---

#### `POST /api/v1/auth/refresh`

Obtain a new access token using a refresh token.

**Authentication:** Refresh token (httpOnly cookie or body)

**Request (cookie-based):**
```
Cookie: refresh_token=eyJhbGciOiJIUzI1NiIs...
```

**Request (body-based — for TUI and M2M):**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

**Error codes:** `401` (invalid/expired/revoked refresh token)

---

#### `POST /api/v1/auth/logout`

Invalidate the current refresh token. Also accepts API key revocation by key ID.

**Authentication:** Bearer token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "message": "Logged out successfully"
  }
}
```

---

### 5.2 Organization & Admin

---

#### `GET /api/v1/organization`

Get the current organization's details.

**Authentication:** Bearer token or API key (read/admin)

**Response `200 OK`:**
```json
{
  "data": {
    "id": "org_a1b2c3d4",
    "name": "My Solar Farm",
    "slug": "my-solar-farm",
    "logo_url": "https://cdn.example.com/logo.png",
    "timezone": "America/Los_Angeles",
    "currency": "USD",
    "emission_factor": 0.92,
    "is_active": true,
    "created_at": "2026-01-15T08:00:00Z",
    "updated_at": "2026-07-22T12:00:00Z"
  }
}
```

---

#### `PUT /api/v1/organization`

Update organization details.

**Authentication:** Bearer token (admin only)

**Request Body:**
```json
{
  "name": "My Solar Farm LLC",
  "logo_url": "https://cdn.example.com/new-logo.png",
  "timezone": "America/New_York",
  "currency": "USD",
  "emission_factor": 0.85
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "id": "org_a1b2c3d4",
    "name": "My Solar Farm LLC",
    "slug": "my-solar-farm",
    "timezone": "America/New_York",
    "currency": "USD",
    "emission_factor": 0.85,
    "updated_at": "2026-07-22T14:00:00Z"
  }
}
```

**Error codes:** `422` (validation error), `409` (slug conflict)

---

#### `GET /api/v1/users`

List users in the organization.

**Authentication:** Bearer token or API key (admin/write)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `role` | string | — | Filter by role (`admin`, `operator`, `viewer`) |
| `status` | string | — | Filter by status (`active`, `inactive`) |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "user_x9y8z7w6",
      "email": "admin@mysolar.com",
      "display_name": "Alex Admin",
      "role": "admin",
      "is_active": true,
      "last_login_at": "2026-07-22T11:00:00Z",
      "created_at": "2026-01-15T08:00:00Z"
    },
    {
      "id": "user_a1b2c3d4",
      "email": "operator@mysolar.com",
      "display_name": "Ophelia Operator",
      "role": "operator",
      "is_active": true,
      "last_login_at": "2026-07-21T09:30:00Z",
      "created_at": "2026-02-01T10:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6InVzZXJfY..."",
    "has_more": false,
    "total": 3
  }
}
```

---

#### `POST /api/v1/users/invite`

Invite a new user to the organization. An invitation email is sent if email sending is configured.

**Authentication:** Bearer token (admin only)

**Request Body:**
```json
{
  "email": "newuser@mysolar.com",
  "display_name": "New User",
  "role": "operator"
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "user_m4n5b6v7",
    "email": "newuser@mysolar.com",
    "display_name": "New User",
    "role": "operator",
    "is_active": true,
    "created_at": "2026-07-22T14:30:00Z"
  }
}
```

**Error codes:** `409` (email already in organization), `422` (validation error)

---

#### `PUT /api/v1/users/{id}/role`

Change a user's role.

**Authentication:** Bearer token (admin only)

**Request Body:**
```json
{
  "role": "viewer"
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "id": "user_a1b2c3d4",
    "email": "operator@mysolar.com",
    "display_name": "Ophelia Operator",
    "role": "viewer",
    "updated_at": "2026-07-22T15:00:00Z"
  }
}
```

**Error codes:** `403` (cannot change own role), `404` (user not found), `422` (invalid role)

---

#### `GET /api/v1/api-keys`

List API keys for the organization. Key hashes are returned, not raw keys.

**Authentication:** Bearer token (admin only)

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "key_a1b2c3d4",
      "key_prefix": "urja_abc12",
      "name": "SCADA Integration",
      "scope": "write",
      "expires_at": "2027-07-22T00:00:00Z",
      "last_used_at": "2026-07-22T10:00:00Z",
      "is_active": true,
      "created_at": "2026-06-01T08:00:00Z"
    }
  ]
}
```

---

#### `POST /api/v1/api-keys`

Create a new API key. The raw key is returned **once** and cannot be retrieved again.

**Authentication:** Bearer token (admin only)

**Request Body:**
```json
{
  "name": "Grafana Dashboard",
  "scope": "read",
  "expires_at": "2027-07-22T00:00:00Z"
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "key_e5f6g7h8",
    "key_prefix": "urja_z98y7",
    "raw_key": "urja_z98y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2h1g0f",
    "name": "Grafana Dashboard",
    "scope": "read",
    "expires_at": "2027-07-22T00:00:00Z",
    "is_active": true,
    "created_at": "2026-07-22T16:00:00Z"
  }
}
```

**Warning:** Store `raw_key` securely. It will not be shown again.

**Error codes:** `409` (name already exists), `422` (validation error)

---

#### `DELETE /api/v1/api-keys/{id}`

Revoke an API key immediately.

**Authentication:** Bearer token (admin only)

**Response `200 OK`:**
```json
{
  "data": {
    "message": "API key revoked successfully"
  }
}
```

**Error codes:** `404` (key not found)

---

### 5.3 Asset Endpoints

---

#### `GET /api/v1/assets`

List assets with filtering and pagination.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `site_id` | UUID | — | Filter by site |
| `asset_type` | string | — | Filter by type (`solar_panel`, `inverter`, `wind_turbine`, `battery_storage`, `meter`) |
| `status` | string | — | Filter by status (`active`, `inactive`, `maintenance`, `retired`) |
| `q` | string | — | Search by name or code |
| `min_capacity` | number | — | Minimum capacity in kW |
| `max_capacity` | number | — | Maximum capacity in kW |
| `health_min` | number | — | Minimum health score (0–100) |
| `sort_by` | string | `name` | Sort field (`name`, `created_at`, `health_score`, `capacity_kw`) |
| `sort_order` | string | `asc` | Sort order (`asc`, `desc`) |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "asset_a1b2c3d4",
      "site_id": "site_x9y8z7w6",
      "parent_asset_id": null,
      "asset_type": "inverter",
      "name": "Inverter #1",
      "code": "INV-001",
      "serial_number": "SMA-2200-US-78901",
      "manufacturer": "SMA Solar Technology",
      "model": "Sunny Central 2200-US",
      "capacity_kw": 1500.0,
      "latitude": 34.0522,
      "longitude": -118.2437,
      "commissioning_date": "2025-06-15",
      "status": "active",
      "health_score": 94.50,
      "created_at": "2025-06-15T08:00:00Z",
      "updated_at": "2026-07-22T12:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6ImFzc2V0X2..."",
    "has_more": true,
    "total": 32
  }
}
```

---

#### `POST /api/v1/assets`

Create a new asset.

**Authentication:** Bearer token or API key (write/admin)

**Request Body:**
```json
{
  "site_id": "site_x9y8z7w6",
  "parent_asset_id": null,
  "asset_type": "inverter",
  "name": "Inverter #33",
  "code": "INV-033",
  "serial_number": "SMA-2200-US-99999",
  "manufacturer": "SMA Solar Technology",
  "model": "Sunny Central 2200-US",
  "capacity_kw": 1500.0,
  "latitude": 34.0600,
  "longitude": -118.2500,
  "commissioning_date": "2026-07-22",
  "config": {
    "max_power_kw": 1650,
    "mppt_channels": 5,
    "max_input_voltage_v": 1500
  },
  "metadata": {
    "installation_notes": "New expansion unit"
  }
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "asset_m4n5b6v7",
    "site_id": "site_x9y8z7w6",
    "asset_type": "inverter",
    "name": "Inverter #33",
    "code": "INV-033",
    "status": "active",
    "health_score": 100.00,
    "created_at": "2026-07-22T16:30:00Z",
    "updated_at": "2026-07-22T16:30:00Z"
  }
}
```

**Error codes:** `404` (site not found), `409` (code already exists), `422` (validation error)

---

#### `GET /api/v1/assets/{id}`

Get detailed information about a single asset, including its hierarchy (parent, children).

**Authentication:** Bearer token or API key (read or higher)

**Response `200 OK`:**
```json
{
  "data": {
    "id": "asset_a1b2c3d4",
    "site": {
      "id": "site_x9y8z7w6",
      "name": "Solar Array Alpha",
      "code": "ALPHA-01"
    },
    "parent_asset": null,
    "children": [
      {
        "id": "asset_p1q2r3s4",
        "name": "Solar Panel String #1-A",
        "asset_type": "solar_panel",
        "capacity_kw": 8.0,
        "status": "active"
      }
    ],
    "asset_type": "inverter",
    "name": "Inverter #1",
    "code": "INV-001",
    "serial_number": "SMA-2200-US-78901",
    "manufacturer": "SMA Solar Technology",
    "model": "Sunny Central 2200-US",
    "capacity_kw": 1500.0,
    "latitude": 34.0522,
    "longitude": -118.2437,
    "commissioning_date": "2025-06-15",
    "status": "active",
    "health_score": 94.50,
    "config": {
      "max_power_kw": 1650,
      "mppt_channels": 5,
      "max_input_voltage_v": 1500
    },
    "metadata": {},
    "created_at": "2025-06-15T08:00:00Z",
    "updated_at": "2026-07-22T12:00:00Z"
  }
}
```

**Error codes:** `404` (asset not found)

---

#### `PUT /api/v1/assets/{id}`

Update an asset's properties.

**Authentication:** Bearer token or API key (write/admin)

**Request Body:**
```json
{
  "name": "Inverter #1 (Upgraded)",
  "status": "maintenance",
  "config": {
    "max_power_kw": 1700,
    "firmware_version": "2.4.1"
  },
  "metadata": {
    "last_service_date": "2026-07-22"
  }
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "id": "asset_a1b2c3d4",
    "name": "Inverter #1 (Upgraded)",
    "status": "maintenance",
    "updated_at": "2026-07-22T17:00:00Z"
  }
}
```

**Error codes:** `404` (asset not found), `409` (code conflict), `422` (validation error)

---

#### `DELETE /api/v1/assets/{id}`

Decommission (soft-delete) an asset. Sets status to `retired`.

**Authentication:** Bearer token or API key (admin)

**Response `200 OK`:**
```json
{
  "data": {
    "message": "Asset decommissioned successfully",
    "asset_id": "asset_a1b2c3d4",
    "status": "retired"
  }
}
```

**Error codes:** `404` (asset not found), `409` (asset has active children)

---

#### `GET /api/v1/sites`

List sites.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `status` | string | — | Filter by status |
| `q` | string | — | Search by name or code |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "site_x9y8z7w6",
      "name": "Solar Array Alpha",
      "code": "ALPHA-01",
      "description": "Main solar array — 15MW capacity",
      "address": "123 Solar Lane, Los Angeles, CA",
      "latitude": 34.0522,
      "longitude": -118.2437,
      "capacity_mw": 15.0,
      "timezone": "America/Los_Angeles",
      "status": "active",
      "asset_count": 12501,
      "created_at": "2025-06-01T08:00:00Z",
      "updated_at": "2026-07-22T12:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 4
  }
}
```

---

#### `POST /api/v1/sites`

Create a new site.

**Authentication:** Bearer token or API key (write/admin)

**Request Body:**
```json
{
  "name": "Solar Array Epsilon",
  "code": "EPSILON-01",
  "description": "New expansion site — 8MW capacity",
  "address": "456 Sun Road, Bakersfield, CA",
  "latitude": 35.3733,
  "longitude": -119.0187,
  "capacity_mw": 8.0,
  "timezone": "America/Los_Angeles",
  "metadata": {
    "grid_connection_point": "Substation B-3",
    "utility": "PG&E"
  }
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "site_p9o8i7u6",
    "name": "Solar Array Epsilon",
    "code": "EPSILON-01",
    "capacity_mw": 8.0,
    "status": "active",
    "created_at": "2026-07-22T18:00:00Z"
  }
}
```

**Error codes:** `409` (code already exists), `422` (validation error)

---

#### `GET /api/v1/sites/{id}`

Get site details with its assets summary.

**Authentication:** Bearer token or API key (read or higher)

**Response `200 OK`:**
```json
{
  "data": {
    "id": "site_x9y8z7w6",
    "name": "Solar Array Alpha",
    "code": "ALPHA-01",
    "capacity_mw": 15.0,
    "status": "active",
    "asset_summary": {
      "total": 12501,
      "by_type": {
        "inverter": 10,
        "solar_panel": 12490,
        "meter": 1
      },
      "by_status": {
        "active": 12495,
        "maintenance": 5,
        "retired": 1
      },
      "active_capacity_kw": 14950.0
    },
    "recent_generation_kwh": 84720.5,
    "created_at": "2025-06-01T08:00:00Z",
    "updated_at": "2026-07-22T12:00:00Z"
  }
}
```

**Error codes:** `404` (site not found)

---

### 5.4 Telemetry Endpoints

---

#### `POST /api/v1/telemetry`

Ingest telemetry data points. Accepts single or batch (up to 1,000 records per request).

**Authentication:** Bearer token or API key (write/admin)

**Rate limit:** 10,000 req/min for API keys, 5,000 req/min for JWT admin

**Request Body (single):**
```json
{
  "asset_id": "asset_a1b2c3d4",
  "ts": "2026-07-22T12:00:00Z",
  "generation_kw": 1250.5,
  "energy_kwh": 312.6,
  "power_factor": 0.95,
  "voltage_v": 480.2,
  "current_a": 2601.0,
  "frequency_hz": 60.02,
  "temperature_c": 42.5,
  "quality_code": 0
}
```

**Request Body (batch):**
```json
{
  "records": [
    {
      "asset_id": "asset_a1b2c3d4",
      "ts": "2026-07-22T12:00:00Z",
      "generation_kw": 1250.5,
      "energy_kwh": 312.6,
      "quality_code": 0
    },
    {
      "asset_id": "asset_b5c6d7e8",
      "ts": "2026-07-22T12:00:00Z",
      "generation_kw": 980.2,
      "energy_kwh": 245.1,
      "quality_code": 0
    }
  ]
}
```

**Response `202 Accepted`:**
```json
{
  "data": {
    "batch_id": "batch_f9e8d7c6",
    "records_accepted": 2,
    "records_rejected": 0,
    "errors": [],
    "status": "processing"
  }
}
```

**Response `200 OK` (when sync processing succeeds — small batches):**
```json
{
  "data": {
    "batch_id": "batch_f9e8d7c6",
    "records_accepted": 1,
    "records_rejected": 0,
    "errors": [],
    "status": "completed"
  }
}
```

**Error codes:** `422` (validation error — field-level), `413` (batch too large > 1000), `429` (rate limited)

---

#### `GET /api/v1/telemetry`

Query telemetry data with time range, asset filtering, and aggregation.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `asset_id` | UUID | Yes | — | Asset to query |
| `start_date` | ISO 8601 | Yes | — | Start of time range |
| `end_date` | ISO 8601 | No | `now()` | End of time range |
| `aggregation` | string | No | `raw` | `raw`, `hourly`, `daily` |
| `granularity` | string | No | — | `15m`, `1h`, `1d` (overrides aggregation) |
| `metrics` | string | No | `generation_kw` | Comma-separated: `generation_kw,energy_kwh,temperature_c` |
| `per_page` | integer | No | `1000` | Max records to return |

**Response `200 OK` (raw):**
```json
{
  "data": [
    {
      "ts": "2026-07-22T12:00:00Z",
      "asset_id": "asset_a1b2c3d4",
      "generation_kw": 1250.5,
      "energy_kwh": 312.6,
      "temperature_c": 42.5,
      "power_factor": 0.95,
      "quality_code": 0
    },
    {
      "ts": "2026-07-22T12:15:00Z",
      "asset_id": "asset_a1b2c3d4",
      "generation_kw": 1260.1,
      "energy_kwh": 315.0,
      "temperature_c": 42.8,
      "power_factor": 0.96,
      "quality_code": 0
    }
  ],
  "pagination": {
    "next_cursor": "eyJzbyI6IjIwMjYtMDctMjJUMTI6MTU6MDBaIn0=",
    "has_more": false,
    "total": 96
  }
}
```

**Response `200 OK` (hourly aggregation):**
```json
{
  "data": [
    {
      "bucket": "2026-07-22T12:00:00Z",
      "asset_id": "asset_a1b2c3d4",
      "avg_kw": 1245.3,
      "peak_kw": 1260.1,
      "min_kw": 1220.0,
      "energy_kwh": 4981.2,
      "reading_count": 4
    }
  ]
}
```

**Error codes:** `400` (invalid date range), `404` (asset not found), `422` (invalid aggregation type)

---

#### `GET /api/v1/telemetry/latest`

Get the latest telemetry reading for every active asset (or a specific asset).

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `asset_id` | UUID | — | Specific asset (omit for all assets) |
| `site_id` | UUID | — | Filter by site |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "asset_id": "asset_a1b2c3d4",
      "asset_name": "Inverter #1",
      "asset_type": "inverter",
      "site_name": "Solar Array Alpha",
      "ts": "2026-07-22T12:00:00Z",
      "generation_kw": 1250.5,
      "energy_kwh": 312.6,
      "temperature_c": 42.5,
      "health_score": 94.5,
      "status": "active"
    }
  ]
}
```

---

### 5.5 Curtailment & Dispatch Endpoints

---

#### `GET /api/v1/curtailment/events`

List curtailment events with filtering and pagination.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `asset_id` | UUID | — | Filter by asset |
| `site_id` | UUID | — | Filter by site |
| `start_date` | ISO 8601 | — | Start of time range |
| `end_date` | ISO 8601 | — | End of time range |
| `is_resolved` | boolean | — | Filter by resolution status |
| `min_revenue_lost` | number | — | Minimum revenue lost (currency units) |
| `sort_by` | string | `ts` | Sort field |
| `sort_order` | string | `desc` | Sort order |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "event_id": "evt_a1b2c3d4",
      "asset_id": "asset_a1b2c3d4",
      "asset_name": "Inverter #1",
      "site_name": "Solar Array Alpha",
      "ts": "2026-07-22T11:00:00Z",
      "duration_minutes": 90,
      "expected_kwh": 1875.0,
      "actual_kwh": 450.0,
      "curtailed_kwh": 1425.0,
      "price_per_kwh": 0.12,
      "revenue_lost": 171.00,
      "grid_price_source": "day_ahead",
      "is_resolved": false,
      "resolved_at": null
    }
  ],
  "pagination": {
    "next_cursor": "eyJ0cyI6IjIwMjYtMDctMjJUMTE6MDA6MDBaIn0=",
    "has_more": true,
    "total": 18
  }
}
```

---

#### `GET /api/v1/curtailment/revenue-lost`

Aggregated revenue loss calculation over a time period.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `start_date` | ISO 8601 | Yes | — | Start of calculation period |
| `end_date` | ISO 8601 | No | `now()` | End of calculation period |
| `site_id` | UUID | No | — | Filter by site |
| `asset_id` | UUID | No | — | Filter by asset |
| `granularity` | string | No | `total` | `total`, `daily`, `monthly`, `by_asset` |

**Response `200 OK` (granularity=total):**
```json
{
  "data": {
    "start_date": "2026-07-01T00:00:00Z",
    "end_date": "2026-07-22T23:59:59Z",
    "total_curtailed_kwh": 48250.0,
    "total_revenue_lost": 5790.00,
    "currency": "USD",
    "event_count": 18,
    "avg_price_per_kwh": 0.12,
    "by_site": [
      {
        "site_id": "site_x9y8z7w6",
        "site_name": "Solar Array Alpha",
        "curtailed_kwh": 15200.0,
        "revenue_lost": 1824.00
      }
    ]
  }
}
```

---

#### `GET /api/v1/dispatch/rules`

List dispatch rules.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `is_active` | boolean | — | Filter by active status |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "rule_a1b2c3d4",
      "name": "Price Spike Battery Discharge",
      "description": "Discharge battery when grid price exceeds $0.30/kWh",
      "is_active": true,
      "priority": 100,
      "condition_type": "price_above",
      "condition_config": {
        "threshold": 0.30,
        "currency": "USD"
      },
      "action": "discharge_battery",
      "action_config": {
        "max_rate_kw": 500,
        "min_soc_pct": 20
      },
      "target_asset_type": "battery_storage",
      "cooldown_minutes": 15,
      "last_triggered_at": "2026-07-20T16:30:00Z",
      "created_at": "2026-01-15T08:00:00Z",
      "updated_at": "2026-07-01T10:00:00Z"
    }
  ]
}
```

---

#### `POST /api/v1/dispatch/rules`

Create a dispatch rule.

**Authentication:** Bearer token or API key (write/admin)

**Request Body:**
```json
{
  "name": "High Generation Compute Routing",
  "description": "Route excess generation to compute load when generation > 80% capacity and curtailment detected",
  "priority": 90,
  "condition_type": "generation_above",
  "condition_config": {
    "threshold_pct": 80,
    "window_minutes": 15
  },
  "action": "route_to_compute",
  "action_config": {
    "target_kw": 200,
    "min_duration_minutes": 30
  },
  "target_asset_type": "inverter",
  "cooldown_minutes": 30
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "rule_f9e8d7c6",
    "name": "High Generation Compute Routing",
    "is_active": true,
    "priority": 90,
    "condition_type": "generation_above",
    "action": "route_to_compute",
    "cooldown_minutes": 30,
    "created_at": "2026-07-22T19:00:00Z"
  }
}
```

**Error codes:** `422` (validation error), `409` (rule name already exists)

---

#### `PUT /api/v1/dispatch/rules/{id}`

Update a dispatch rule.

**Authentication:** Bearer token or API key (write/admin)

**Request Body:**
```json
{
  "name": "High Generation Compute Routing v2",
  "priority": 85,
  "condition_config": {
    "threshold_pct": 85,
    "window_minutes": 10
  },
  "is_active": false
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "id": "rule_f9e8d7c6",
    "name": "High Generation Compute Routing v2",
    "is_active": false,
    "priority": 85,
    "updated_at": "2026-07-22T19:15:00Z"
  }
}
```

**Error codes:** `404` (rule not found), `422` (validation error)

---

#### `GET /api/v1/dispatch/decisions`

History of dispatch decisions with filtering.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `rule_id` | UUID | — | Filter by rule |
| `asset_id` | UUID | — | Filter by asset |
| `status` | string | — | Filter by status (`pending`, `executed`, `failed`, `skipped`) |
| `start_date` | ISO 8601 | — | Start date |
| `end_date` | ISO 8601 | — | End date |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "dec_a1b2c3d4",
      "rule_name": "Price Spike Battery Discharge",
      "asset_name": "Battery #1",
      "status": "executed",
      "action_taken": "discharge_battery",
      "action_params": {
        "rate_kw": 500,
        "target_soc_pct": 20
      },
      "triggered_value": 0.32,
      "expected_outcome": 45.00,
      "actual_outcome": 44.80,
      "duration_seconds": 1800,
      "executed_at": "2026-07-22T12:30:00Z",
      "created_at": "2026-07-22T12:30:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 145
  }
}
```

---

### 5.6 Carbon Endpoints

---

#### `GET /api/v1/carbon/credits`

List carbon credits with filtering and pagination.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `status` | string | — | `pending`, `active`, `retired`, `cancelled` |
| `asset_id` | UUID | — | Filter by asset |
| `batch_id` | UUID | — | Filter by batch |
| `start_date` | ISO 8601 | — | Generation period start |
| `end_date` | ISO 8601 | — | Generation period end |
| `sort_by` | string | `ts` | Sort field |
| `sort_order` | string | `desc` | Sort order |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "credit_id": "cred_a1b2c3d4",
      "batch_id": "batch_f9e8d7c6",
      "asset_id": "asset_a1b2c3d4",
      "asset_name": "Inverter #1",
      "status": "active",
      "quantity": 1.0,
      "unit": "tCO2e",
      "methodology": "IPMVP_v2.1",
      "generation_start": "2026-06-01T00:00:00Z",
      "generation_end": "2026-06-30T23:59:59Z",
      "total_kwh": 1087.0,
      "emission_factor": 0.92,
      "registry_tx_id": "VCS-2026-06-001",
      "registry_url": "https://registry.verra.org/credit/VCS-2026-06-001",
      "issued_by": "user_x9y8z7w6",
      "retired_at": null,
      "notes": "June 2026 generation batch",
      "created_at": "2026-07-01T08:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJ0cyI6IjIwMjYtMDctMDFUMDg6MDA6MDBaIn0=",
    "has_more": true,
    "total": 420
  }
}
```

---

#### `POST /api/v1/carbon/issue`

Issue new carbon credits from generation data. This triggers the MRV pipeline: calculates CO2 equivalent, creates credit records, and pushes audit trail to registry.

**Authentication:** Bearer token or API key (write/admin)

**Idempotency:** Supported via `Idempotency-Key` header.

**Request Body:**
```json
{
  "asset_id": "asset_a1b2c3d4",
  "generation_start": "2026-06-01T00:00:00Z",
  "generation_end": "2026-06-30T23:59:59Z",
  "methodology": "IPMVP_v2.1",
  "notes": "June 2026 monthly mint"
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "batch_id": "batch_f9e8d7c6",
    "total_kwh": 1087000.0,
    "emission_factor": 0.92,
    "total_co2e": 1000.04,
    "credit_count": 1000,
    "credit_ids": ["cred_a1b2c3d4", "cred_e5f6g7h8", "..."],
    "methodology": "IPMVP_v2.1",
    "registry_tx_id": "VCS-2026-06-001",
    "status": "active",
    "created_at": "2026-07-01T08:00:00Z"
  }
}
```

**Error codes:** `400` (generation range exceeds 1 year), `404` (asset not found), `409` (credits already issued for this range — use `Idempotency-Key`), `422` (validation error)

---

#### `GET /api/v1/carbon/credits/{id}`

Get detailed information about a specific carbon credit, including full audit trail.

**Authentication:** Bearer token or API key (read or higher)

**Response `200 OK`:**
```json
{
  "data": {
    "credit_id": "cred_a1b2c3d4",
    "batch_id": "batch_f9e8d7c6",
    "asset": {
      "id": "asset_a1b2c3d4",
      "name": "Inverter #1",
      "code": "INV-001"
    },
    "organization_id": "org_a1b2c3d4",
    "status": "active",
    "quantity": 1.0,
    "unit": "tCO2e",
    "methodology": "IPMVP_v2.1",
    "generation_start": "2026-06-01T00:00:00Z",
    "generation_end": "2026-06-30T23:59:59Z",
    "total_kwh": 1087.0,
    "emission_factor": 0.92,
    "registry_tx_id": "VCS-2026-06-001",
    "registry_url": "https://registry.verra.org/credit/VCS-2026-06-001",
    "issued_by": "user_x9y8z7w6",
    "retired_at": null,
    "notes": "June 2026 generation batch",
    "audit_trail": [
      {
        "action": "credit.created",
        "actor": "user_x9y8z7w6",
        "timestamp": "2026-07-01T08:00:00Z",
        "details": "Credit created from generation batch batch_f9e8d7c6"
      },
      {
        "action": "credit.issued",
        "actor": "system",
        "timestamp": "2026-07-01T08:00:05Z",
        "details": "Registry transaction submitted (tx: VCS-2026-06-001)"
      }
    ],
    "created_at": "2026-07-01T08:00:00Z"
  }
}
```

**Error codes:** `404` (credit not found)

---

#### `GET /api/v1/carbon/portfolio`

Portfolio summary — total issued, retired, available credits.

**Authentication:** Bearer token or API key (read or higher)

**Response `200 OK`:**
```json
{
  "data": {
    "total_issued": 5000,
    "total_retired": 750,
    "total_cancelled": 25,
    "total_available": 4225,
    "total_co2e_issued": 5000.0,
    "total_co2e_retired": 750.0,
    "currency": "USD",
    "estimated_value": 250000.00,
    "price_per_credit": 50.00,
    "by_status": {
      "active": 4225,
      "retired": 750,
      "cancelled": 25,
      "pending": 0
    },
    "by_methodology": {
      "IPMVP_v2.1": 5000
    },
    "last_issuance": "2026-07-01T08:00:00Z",
    "next_eligible_date": "2026-08-01T00:00:00Z"
  }
}
```

---

#### `GET /api/v1/carbon/mrv-pipeline`

MRV pipeline status and logs — shows the processing status of credit issuance batches.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `status` | string | — | `pending`, `processing`, `completed`, `failed` |
| `limit` | integer | `10` | Number of batches to return |

**Response `200 OK`:**
```json
{
  "data": {
    "pipeline_status": "operational",
    "last_sync": "2026-07-22T12:00:00Z",
    "pending_batches": 1,
    "processing_batches": 0,
    "failed_batches": 0,
    "recent_batches": [
      {
        "batch_id": "batch_f9e8d7c6",
        "status": "completed",
        "methodology": "IPMVP_v2.1",
        "total_kwh": 1087000.0,
        "total_co2e": 1000.04,
        "credit_count": 1000,
        "registry_tx_id": "VCS-2026-06-001",
        "started_at": "2026-07-01T08:00:00Z",
        "completed_at": "2026-07-01T08:00:10Z",
        "duration_seconds": 10,
        "error": null
      },
      {
        "batch_id": "batch_p9o8i7u6",
        "status": "pending",
        "methodology": "IPMVP_v2.1",
        "total_kwh": null,
        "total_co2e": null,
        "credit_count": null,
        "registry_tx_id": null,
        "started_at": null,
        "completed_at": null,
        "duration_seconds": null,
        "error": null
      }
    ]
  }
}
```

---

### 5.7 Health Endpoints

---

#### `GET /api/v1/health/scores`

Health scores per asset.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `site_id` | UUID | — | Filter by site |
| `asset_id` | UUID | — | Specific asset |
| `status` | string | `active` | Asset status filter |
| `health_max` | number | — | Max health score (e.g., 80 for underperformers) |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "asset_id": "asset_a1b2c3d4",
      "asset_name": "Inverter #1",
      "asset_type": "inverter",
      "site_name": "Solar Array Alpha",
      "health_score": 94.5,
      "anomaly_score": 0.02,
      "trend": "stable",
      "metric_scores": {
        "power_kw": 95.5,
        "temperature_c": 88.2,
        "voltage_v": 97.1
      },
      "anomaly_flags": [],
      "last_checked_at": "2026-07-22T12:00:00Z"
    },
    {
      "asset_id": "asset_b5c6d7e8",
      "asset_name": "Inverter #7",
      "asset_type": "inverter",
      "site_name": "Solar Array Alpha",
      "health_score": 72.3,
      "anomaly_score": 0.15,
      "trend": "declining",
      "metric_scores": {
        "power_kw": 68.0,
        "temperature_c": 75.0,
        "voltage_v": 82.5
      },
      "anomaly_flags": ["power_drop_alert"],
      "last_checked_at": "2026-07-22T12:00:00Z"
    }
  ]
}
```

---

#### `GET /api/v1/health/alerts`

Active and historical alerts.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `status` | string | — | `active`, `acknowledged`, `resolved` |
| `severity` | string | — | `warning`, `critical` |
| `asset_id` | UUID | — | Filter by asset |
| `start_date` | ISO 8601 | — | Alert created after |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "alert_a1b2c3d4",
      "asset_id": "asset_b5c6d7e8",
      "asset_name": "Inverter #7",
      "site_name": "Solar Array Alpha",
      "metric": "generation_kw",
      "severity": "critical",
      "status": "active",
      "observed_value": 680.0,
      "expected_value": 1200.0,
      "deviation_pct": 43.3,
      "message": "Power output dropped 43.3% below expected for 15+ minutes",
      "threshold_config": {
        "deviation_pct": 20,
        "duration_minutes": 15
      },
      "triggered_at": "2026-07-22T11:45:00Z",
      "acknowledged_at": null,
      "acknowledged_by": null,
      "resolved_at": null,
      "created_at": "2026-07-22T11:45:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 12
  }
}
```

---

#### `PUT /api/v1/health/alerts/{id}/acknowledge`

Acknowledge an alert. Moves it from `active` to `acknowledged` status.

**Authentication:** Bearer token or API key (write/admin)

**Response `200 OK`:**
```json
{
  "data": {
    "id": "alert_a1b2c3d4",
    "status": "acknowledged",
    "acknowledged_at": "2026-07-22T14:00:00Z",
    "acknowledged_by": "user_x9y8z7w6"
  }
}
```

**Error codes:** `404` (alert not found), `409` (alert already acknowledged/resolved)

---

#### `GET /api/v1/health/anomalies`

Anomaly detection logs.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `asset_id` | UUID | — | Filter by asset |
| `start_date` | ISO 8601 | — | Start date |
| `end_date` | ISO 8601 | — | End date |
| `min_score` | number | — | Minimum anomaly score |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "anom_a1b2c3d4",
      "asset_id": "asset_b5c6d7e8",
      "asset_name": "Inverter #7",
      "ts": "2026-07-22T11:45:00Z",
      "metric": "generation_kw",
      "observed_value": 680.0,
      "expected_value": 1200.0,
      "z_score": 3.45,
      "anomaly_score": 0.15,
      "method": "z_score",
      "window_size": 96,
      "triggered_alert_id": "alert_a1b2c3d4",
      "created_at": "2026-07-22T11:45:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 85
  }
}
```

---

#### `GET /api/v1/maintenance/work-orders`

List work orders.

**Authentication:** Bearer token or API key (read or higher)

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Pagination cursor |
| `per_page` | integer | `20` | Items per page |
| `status` | string | — | `scheduled`, `in_progress`, `completed`, `cancelled`, `deferred` |
| `priority` | string | — | `low`, `medium`, `high`, `critical` |
| `asset_id` | UUID | — | Filter by asset |
| `assigned_to` | UUID | — | Filter by assignee |
| `overdue` | boolean | — | Only overdue work orders |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "wo_a1b2c3d4",
      "asset_id": "asset_b5c6d7e8",
      "asset_name": "Inverter #7",
      "site_name": "Solar Array Alpha",
      "alert_id": "alert_a1b2c3d4",
      "assigned_to": {
        "id": "user_a1b2c3d4",
        "display_name": "Ophelia Operator"
      },
      "title": "Inverter #7 — Power output investigation",
      "description": "Investigate 43% power drop detected at 11:45. Possible MPPT failure.",
      "priority": "high",
      "status": "in_progress",
      "scheduled_start": "2026-07-22T14:00:00Z",
      "scheduled_end": "2026-07-22T17:00:00Z",
      "actual_start": "2026-07-22T14:15:00Z",
      "actual_end": null,
      "estimated_cost": 500.00,
      "actual_cost": null,
      "parts_used": [],
      "resolution_notes": null,
      "created_at": "2026-07-22T12:00:00Z",
      "updated_at": "2026-07-22T14:15:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 50
  }
}
```

---

#### `POST /api/v1/maintenance/work-orders`

Create a new work order.

**Authentication:** Bearer token or API key (write/admin)

**Request Body:**
```json
{
  "asset_id": "asset_b5c6d7e8",
  "alert_id": "alert_a1b2c3d4",
  "assigned_to": "user_a1b2c3d4",
  "title": "Inverter #7 — Power output investigation",
  "description": "Investigate 43% power drop detected at 11:45. Possible MPPT failure.",
  "priority": "high",
  "scheduled_start": "2026-07-22T14:00:00Z",
  "scheduled_end": "2026-07-22T17:00:00Z",
  "estimated_cost": 500.00
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "wo_f9e8d7c6",
    "asset_id": "asset_b5c6d7e8",
    "title": "Inverter #7 — Power output investigation",
    "priority": "high",
    "status": "scheduled",
    "scheduled_start": "2026-07-22T14:00:00Z",
    "scheduled_end": "2026-07-22T17:00:00Z",
    "created_at": "2026-07-22T12:05:00Z"
  }
}
```

**Error codes:** `404` (asset or user not found), `422` (validation error)

---

#### `PUT /api/v1/maintenance/work-orders/{id}`

Update a work order (status, assignment, notes, costs, etc.).

**Authentication:** Bearer token or API key (write/admin)

**Request Body:**
```json
{
  "status": "completed",
  "actual_start": "2026-07-22T14:15:00Z",
  "actual_end": "2026-07-22T16:30:00Z",
  "actual_cost": 450.00,
  "parts_used": [
    {"name": "Fuse 15A", "quantity": 2, "cost": 15.00},
    {"name": "Thermal paste", "quantity": 1, "cost": 8.50}
  ],
  "resolution_notes": "Replaced blown fuse on MPPT channel 3. Thermal paste applied to heat sink. All readings normal after repair."
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "id": "wo_f9e8d7c6",
    "status": "completed",
    "actual_start": "2026-07-22T14:15:00Z",
    "actual_end": "2026-07-22T16:30:00Z",
    "actual_cost": 450.00,
    "updated_at": "2026-07-22T16:30:00Z"
  }
}
```

**Error codes:** `404` (work order not found), `422` (validation error — e.g., `actual_end` before `actual_start`)

---

## 6. Common Error Codes

### 6.1 HTTP Status Code Summary

| Code | Name | When |
|---|---|---|
| `200` | OK | Successful GET, PUT |
| `201` | Created | Successful POST (resource created) |
| `202` | Accepted | Asynchronous operation accepted (telemetry ingest, carbon mint) |
| `204` | No Content | Successful DELETE |
| `400` | Bad Request | Malformed request, invalid query parameters |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Authenticated but insufficient permissions |
| `404` | Not Found | Resource does not exist |
| `409` | Conflict | Resource already exists (duplicate code, email, name) |
| `413` | Payload Too Large | Batch exceeds maximum size |
| `422` | Unprocessable Entity | Request body validation failed (field-level errors) |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |
| `503` | Service Unavailable | Server is temporarily unable to handle request |

### 6.2 Standard Error Response Format

All errors follow RFC 7807 (Problem Details for HTTP APIs):

```json
{
  "type": "https://api.urja.dev/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request body contains invalid fields.",
  "instance": "/api/v1/assets",
  "errors": [
    {
      "field": "capacity_kw",
      "message": "Must be greater than 0",
      "code": "greater_than"
    }
  ],
  "meta": {
    "request_id": "req_a1b2c3d4",
    "timestamp": "2026-07-22T12:00:00Z"
  }
}
```

### 6.3 Common Error Types

| `type` URI | `title` | Typical `status` |
|---|---|---|
| `/errors/validation-error` | Validation Error | `422` |
| `/errors/authentication-error` | Authentication Error | `401` |
| `/errors/authorization-error` | Forbidden | `403` |
| `/errors/not-found` | Not Found | `404` |
| `/errors/conflict` | Resource Conflict | `409` |
| `/errors/rate-limited` | Rate Limit Exceeded | `429` |
| `/errors/payload-too-large` | Payload Too Large | `413` |
| `/errors/internal-error` | Internal Server Error | `500` |
| `/errors/service-unavailable` | Service Unavailable | `503` |

---

## 7. Example Workflows

### 7.1 Full Walkthrough: Authenticate → Create Asset → Ingest Telemetry → Detect Curtailment → Issue Carbon Credit

**Step 1: Register or Login**

```bash
# Register a new organization
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Demo Solar Farm",
    "organization_slug": "demo-solar",
    "email": "admin@demo-solar.com",
    "password": "urja-demo-2026",
    "display_name": "Admin User"
  }'
```

**Response:** Save the `access_token` and `refresh_token`.

```bash
# Or login if already registered
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo-solar.com",
    "password": "urja-demo-2026"
  }'
```

**Step 2: Create a Site**

```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."

curl -X POST http://localhost:8000/api/v1/sites \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Solar Array Demo",
    "code": "DEMO-01",
    "capacity_mw": 5.0,
    "latitude": 34.0522,
    "longitude": -118.2437,
    "timezone": "America/Los_Angeles"
  }'
```

**Response:** Save `site_id` (e.g., `site_x9y8z7w6`).

**Step 3: Create an Asset**

```bash
curl -X POST http://localhost:8000/api/v1/assets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "site_id": "site_x9y8z7w6",
    "asset_type": "inverter",
    "name": "Demo Inverter #1",
    "code": "DEMO-INV-001",
    "capacity_kw": 1500.0,
    "latitude": 34.0522,
    "longitude": -118.2437,
    "commissioning_date": "2026-07-22"
  }'
```

**Response:** Save `asset_id` (e.g., `asset_a1b2c3d4`).

**Step 4: Ingest Telemetry**

```bash
# Single reading
curl -X POST http://localhost:8000/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "asset_id": "asset_a1b2c3d4",
    "ts": "2026-07-22T12:00:00Z",
    "generation_kw": 1250.5,
    "energy_kwh": 312.6,
    "temperature_c": 42.5,
    "quality_code": 0
  }'

# Batch (for backfill or bulk ingest)
curl -X POST http://localhost:8000/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "records": [
      {"asset_id": "asset_a1b2c3d4", "ts": "2026-07-22T11:00:00Z", "generation_kw": 900.0, "quality_code": 0},
      {"asset_id": "asset_a1b2c3d4", "ts": "2026-07-22T11:15:00Z", "generation_kw": 850.0, "quality_code": 0},
      {"asset_id": "asset_a1b2c3d4", "ts": "2026-07-22T11:30:00Z", "generation_kw": 200.0, "quality_code": 0},
      {"asset_id": "asset_a1b2c3d4", "ts": "2026-07-22T11:45:00Z", "generation_kw": 150.0, "quality_code": 0}
    ]
  }'
```

**Step 5: Query Latest Telemetry**

```bash
curl -X GET "http://localhost:8000/api/v1/telemetry/latest?asset_id=asset_a1b2c3d4" \
  -H "Authorization: Bearer $TOKEN"
```

**Step 6: Check Curtailment Events**

```bash
curl -X GET "http://localhost:8000/api/v1/curtailment/events?asset_id=asset_a1b2c3d4&start_date=2026-07-22T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN"
```

The yield service automatically detects curtailment when generation drops below expected (based on irradiance model or historical baseline).

**Step 7: Check Revenue Lost**

```bash
curl -X GET "http://localhost:8000/api/v1/curtailment/revenue-lost?start_date=2026-07-01T00:00:00Z&end_date=2026-07-22T23:59:59Z" \
  -H "Authorization: Bearer $TOKEN"
```

**Step 8: Configure Dispatch Rules**

```bash
curl -X POST http://localhost:8000/api/v1/dispatch/rules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Low Price Battery Charge",
    "condition_type": "price_below",
    "condition_config": {"threshold": 0.05, "currency": "USD"},
    "action": "charge_battery",
    "action_config": {"target_soc_pct": 90, "max_rate_kw": 500},
    "priority": 90
  }'
```

**Step 9: Issue Carbon Credits**

```bash
curl -X POST http://localhost:8000/api/v1/carbon/issue \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: idemp_demo_july_001" \
  -d '{
    "asset_id": "asset_a1b2c3d4",
    "generation_start": "2026-07-01T00:00:00Z",
    "generation_end": "2026-07-22T23:59:59Z",
    "methodology": "IPMVP_v2.1",
    "notes": "Demo issuance for July 2026"
  }'
```

**Step 10: Check Carbon Portfolio**

```bash
curl -X GET http://localhost:8000/api/v1/carbon/portfolio \
  -H "Authorization: Bearer $TOKEN"
```

### 7.2 M2M Integration: API Key Setup

```bash
# 1. Create an API key (admin only)
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "SCADA Integration",
    "scope": "write",
    "expires_at": "2027-07-22T00:00:00Z"
  }'

# Response includes the raw key — save it securely!
# { "raw_key": "urja_z98y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2h1g0f" }

# 2. Use API key for telemetry ingestion
curl -X POST http://localhost:8000/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -H "X-API-Key: urja_z98y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2h1g0f" \
  -d '{
    "asset_id": "asset_a1b2c3d4",
    "ts": "2026-07-22T13:00:00Z",
    "generation_kw": 1100.0,
    "quality_code": 0
  }'

# 3. Query data with API key
curl -X GET "http://localhost:8000/api/v1/telemetry/latest" \
  -H "X-API-Key: urja_z98y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2h1g0f"
```

### 7.3 TUI Polling Pattern

The Textual TUI polls the API at a configurable interval (default 15 seconds). A typical poll cycle fetches:

```bash
# Fetch latest telemetry for all assets
curl -X GET http://localhost:8000/api/v1/telemetry/latest \
  -H "Authorization: Bearer $TOKEN"

# Fetch active alerts (top 5)
curl -X GET "http://localhost:8000/api/v1/health/alerts?status=active&per_page=5" \
  -H "Authorization: Bearer $TOKEN"

# Fetch curtailment events (today)
curl -X GET "http://localhost:8000/api/v1/curtailment/events?start_date=2026-07-22T00:00:00Z&per_page=10" \
  -H "Authorization: Bearer $TOKEN"

# Fetch carbon portfolio summary
curl -X GET http://localhost:8000/api/v1/carbon/portfolio \
  -H "Authorization: Bearer $TOKEN"

# Fetch health scores
curl -X GET "http://localhost:8000/api/v1/health/scores?status=active" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. SDK & Client Generation

### 8.1 Auto-Generated OpenAPI Spec

The FastAPI server auto-generates an OpenAPI 3.1 specification. Two browser interfaces are available:

| URL | Description |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — interactive endpoint testing |
| `http://localhost:8000/redoc` | ReDoc — clean documentation view |

The raw OpenAPI JSON spec is available at:

```bash
curl -X GET http://localhost:8000/openapi.json
```

### 8.2 Client Generation

The OpenAPI spec can be used to generate typed API clients in any language:

**Python (using `openapi-python-client`):**
```bash
pip install openapi-python-client
openapi-python-client generate --url http://localhost:8000/openapi.json
```

**TypeScript (using `openapi-typescript`):**
```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/types.ts
```

**Go (using `oapi-codegen`):**
```bash
oapi-codegen -package api -generate client http://localhost:8000/openapi.json > api/client.go
```

### 8.3 Frontend API Client

The Next.js frontend includes a typed API client layer in `frontend/src/lib/api/`:

```
frontend/src/lib/api/
├── client.ts          # Base HTTP client with auth injection
├── endpoints/
│   ├── auth.ts        # Auth API calls
│   ├── assets.ts      # Asset API calls
│   ├── telemetry.ts   # Telemetry API calls
│   ├── dispatch.ts    # Curtailment & dispatch API calls
│   ├── carbon.ts      # Carbon API calls
│   └── health.ts      # Health & maintenance API calls
└── types.ts           # Shared TypeScript types (Pydantic → TS)
```

The client layer handles:
- JWT token injection (access token from memory)
- Automatic token refresh on 401 responses
- API key header injection for M2M modes
- Error response parsing (RFC 7807)
- Request/response type validation

### 8.4 TUI API Client

The Textual TUI has its own async API client in `dashboard-tui/api_client.py`:

```python
# dashboard-tui/api_client.py
import httpx
from typing import Any

class UrjaAPIClient:
    def __init__(self, base_url: str, api_key: str | None = None):
        self.client = httpx.AsyncClient(base_url=base_url)
        self.api_key = api_key

    async def get_latest_telemetry(self) -> list[dict[str, Any]]:
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        resp = await self.client.get("/api/v1/telemetry/latest", headers=headers)
        resp.raise_for_status()
        return resp.json()["data"]
```

---

## Appendix A: API Change Log

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-07-22 | v1.0.0 | Initial API specification | API Platform Engineer |

## Appendix B: Related Documents

| Document | Description |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, C4 diagrams, ADRs |
| [DATABASE.md](DATABASE.md) | Complete schema, hypertables, indexing, seed data |
| [PRD.md](../product/PRD.md) | Product requirements, personas, success metrics |

---

*API-SPEC v1.0 — This document is a contract. Every endpoint, schema, and error code documented here is a promise to developers who build on URJA. If you find a discrepancy between this document and the implementation, file an issue. If you need an endpoint that doesn't exist, open a feature request — but be prepared to version it deliberately and deprecate with dignity.*
