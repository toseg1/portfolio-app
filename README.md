# Portfolio App

A web application for tracking and analysing investment portfolios, with a secondary
real estate module. Two audiences: individuals (B2C) and CIF-registered financial
advisors managing a book of clients (B2B).

**The full specification lives in Notion.** This repository is private, and
[`CLAUDE.md`](CLAUDE.md) is the distilled set of working rules that must be honoured
on every change — read it (and `backend/CLAUDE.md`, `frontend/CLAUDE.md`) before
touching anything. [`docs/adr/README.md`](docs/adr/README.md) indexes every
architectural decision.

## Stack

Django 5 + DRF, PostgreSQL (`NUMERIC` for all money, never SQLite), Celery + Redis,
Next.js + TypeScript, Render (EU region). See
[`docs/adr/README.md`](docs/adr/README.md) for the reasoning behind each choice.

## Repository layout

```
backend/     Django + DRF. apps/ mirrors the module list.
frontend/    Next.js — marketing site and app in one.
contracts/   openapi.json + generated/api-types.ts. The boundary.
infra/       docker-compose.yml, render.yaml
docs/        adr/README.md — every decision, one line each
```

One monorepo, not one repository per deployable — see ADR-028.

## Local development

```bash
cp .env.example .env      # fill in the values; .env is git-ignored
docker compose -f infra/docker-compose.yml up
```

This runs `web`, `worker` (Celery, with Beat embedded), `postgres`, `redis` and
`mailpit`. Mailpit is a fake SMTP server — nothing it sends is ever real — with a web
inbox at [http://localhost:8025](http://localhost:8025).

PostgreSQL is used everywhere, including tests — never SQLite, even locally.

## Where to look

- **Notion workspace** — the full specification, all reasoning
- **[`CLAUDE.md`](CLAUDE.md)** — working rules, the five non-negotiables, what must
  never be done
- **[`docs/adr/README.md`](docs/adr/README.md)** — every architectural decision, one
  line each
- Roadmap and Open Questions live in Notion databases
