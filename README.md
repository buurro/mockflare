# mockflare

> ⚠️ **AI-generated code, work in progress, for local development only.** Not affiliated with Cloudflare.

A mock implementation of the Cloudflare API for local development and testing. Supports DNS Records and Custom Hostnames management.

## Quick Start

```bash
uv run fastapi dev
```

Visit http://localhost:8000/docs for the API documentation.

## API Endpoints

### Zones
- `GET /zones` - List zones (with filtering and pagination)
- `GET /zones/{zone_id}` - Get zone
- `POST /zones` - Create zone
- `PATCH /zones/{zone_id}` - Update zone
- `DELETE /zones/{zone_id}` - Delete zone

### DNS Records
- `GET /zones/{zone_id}/dns_records` - List DNS records
- `GET /zones/{zone_id}/dns_records/{record_id}` - Get DNS record
- `POST /zones/{zone_id}/dns_records` - Create DNS record
- `PUT /zones/{zone_id}/dns_records/{record_id}` - Overwrite DNS record
- `PATCH /zones/{zone_id}/dns_records/{record_id}` - Update DNS record
- `DELETE /zones/{zone_id}/dns_records/{record_id}` - Delete DNS record

### Custom Hostnames
- `GET /zones/{zone_id}/custom_hostnames` - List custom hostnames
- `GET /zones/{zone_id}/custom_hostnames/{hostname_id}` - Get custom hostname
- `POST /zones/{zone_id}/custom_hostnames` - Create custom hostname
- `PATCH /zones/{zone_id}/custom_hostnames/{hostname_id}` - Update custom hostname
- `DELETE /zones/{zone_id}/custom_hostnames/{hostname_id}` - Delete custom hostname

#### Status Injection

Custom hostnames default to `status: active` and `ssl.status: active`. To test different states, embed status values in the hostname labels:

| Hostname | Result |
|----------|--------|
| `app.example.com` | `status: active`, `ssl.status: active` |
| `status-pending.example.com` | `status: pending` |
| `ssl-status-pending-validation.example.com` | `ssl.status: pending_validation` |
| `status-blocked.ssl-status-expired.example.com` | Both statuses set |

Use hyphens in the label, they're converted to underscores (e.g., `pending-validation` → `pending_validation`).

Valid values: [`status`](app/models.py#L114), [`ssl.status`](app/models.py#L84)

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./mockflare.db` | Database connection string |
| `CREATE_DB` | `true` | Auto-create database if not found |
| `SEED_DATA` | (empty) | Seed data JSON (see below) |

## Database

Supports SQLite (default) and PostgreSQL:

```bash
# SQLite (default)
DATABASE_URL=sqlite:///./mockflare.db

# PostgreSQL
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/mockflare
```

For PostgreSQL, the database is automatically created if it doesn't exist (requires `CREATEDB` privilege).

## Seed Data

Seed data is loaded on startup if `SEED_DATA` is set to a JSON string. Seeding is idempotent - existing zones are skipped.

```bash
SEED_DATA='{"zones":[{"zone":{"name":"example.com","account_id":"acc-001"}}]}'
```

### Seed Data Schema

```json
{
  "zones": [
    {
      "zone": {
        "id": "optional-zone-id",
        "name": "example.com",
        "account_id": "acc-001"
      },
      "dns_records": [
        {
          "id": "optional-record-id",
          "name": "example.com",
          "type": "A",
          "content": "192.0.2.1",
          "ttl": 3600,
          "proxied": true
        }
      ],
      "custom_hostnames": [
        {
          "id": "optional-hostname-id",
          "hostname": "app.customer.com",
          "status": "active",
          "ssl_status": "active"
        }
      ]
    }
  ]
}
```

All `id` fields are optional - UUIDs are auto-generated if omitted.

## Kubernetes Deployment

Example ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mockflare-config
data:
  DATABASE_URL: postgresql+psycopg://postgres:postgres@postgresql:5432/mockflare
  SEED_DATA: |
    {
      "zones": [{
        "zone": {
          "id": "abc123",
          "name": "myapp.dev",
          "account_id": "acc-001"
        }
      }]
    }
```

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run ty check
```

## Docker

```bash
docker build -t mockflare .
docker run -p 8000:8000 mockflare
```
