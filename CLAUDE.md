# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mockflare is a FastAPI mock implementation of the Cloudflare API for local development and testing. Supports DNS Records and Custom Hostnames management.

## Commands

```bash
# Development server (http://localhost:8000)
uv run fastapi dev

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_zones.py::TestCreateZone::test_create_zone

# Lint and format
uv run ruff check .          # Lint
uv run ruff check --fix .    # Lint with auto-fix
uv run ruff format .         # Format

# Type check
uv run ty check
```

## Architecture

**Stack**: FastAPI + SQLModel + SQLite (default) / PostgreSQL

**Key patterns**:
- Cloudflare-compatible response wrappers via `schemas.py` (`make_response()`, `make_list_response()`)
- Database auto-creation on startup (PostgreSQL databases created if missing)
- Idempotent seeding via `SEED_DATA` env var with Pydantic validation
- Custom hostnames support status injection via hostname labels (e.g., `status-pending.example.com`)

**Structure**:
- `app/main.py` - FastAPI app with lifespan for DB init and seeding
- `app/database.py` - Engine config, DB/table creation (supports PostgreSQL + SQLite)
- `app/models.py` - SQLModel ORM definitions and enums
- `app/schemas.py` - Cloudflare response wrappers (generic type params)
- `app/seed.py` - Seed data models and loading from `SEED_DATA` env var
- `app/routes/` - API endpoints (zones, dns_records, custom_hostnames)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./mockflare.db` | Database connection |
| `CREATE_DB` | `true` | Auto-create database if not found |
| `SEED_DATA` | (empty) | Seed data JSON |
