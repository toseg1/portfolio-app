# Portfolio App — working rules

A web application for tracking and analysing investment portfolios, with a secondary
real estate module. Two audiences: individuals (B2C) and CIF-registered financial
advisors managing a book of clients (B2B).

The full specification lives in Notion. This file is the distilled version that must
be honoured on every change. `docs/adr/README.md` lists every architectural decision.

---

## The most important rule

**If something is not specified in this repo or in the Notion workspace, STOP AND ASK.
Do not design it.**

Every table, column, constraint, index and module behaviour has already been specified.
Inventing schema, adding a field "that seems useful", or resolving an ambiguity by
picking one is a defect, not initiative. Undecided items live in the Open Questions
database and are decided by a human.

---

## The five non-negotiables

### 1. NO investment recommendations

The application describes; it never advises. This is a regulatory boundary, not a
style preference.

**Forbidden everywhere, including copy, tooltips, chart labels and PDF text:**
- Target allocations or optimiser output weights
- Rebalancing trade lists
- Ranking, scoring or suggesting specific instruments
- The language of advice: "you should", "recommended", "optimal for you", "we suggest",
  "best performing", "too concentrated"

The efficient frontier is drawn as a **reference curve**. The optimiser's weight
vectors are dropped inside the Celery task and never serialised to the API, never
stored, never rendered. A cash-heavy portfolio sitting below the curve is never
framed as inefficiency.

Every analytics screen carries a standing disclaimer that the content is informational
and not personalised investment advice.

### 2. Transactions are the source of truth; positions are derived

`Transaction` rows are **immutable**. Holdings, cost basis and performance are computed
from them through one code path. **Never store a mutable "current quantity" as primary
data.** Corrections are compensating rows, never edits.

The only sanctioned replacement is a synthetic `OPENING_BALANCE` row superseded by a
real statement, via `supersedes_transaction_id` / `superseded_at`.

### 3. Never convert currency on write

Store three separate facts: the transaction currency, the FX rate at trade date
(frozen on the transaction row), and the portfolio base currency. Conversion happens
at read time.

**All monetary values are `NUMERIC`. No `float` anywhere in the money path.**
Quantities `NUMERIC(28,10)`, money `NUMERIC(20,4)`, unit price `NUMERIC(20,8)`,
rates and ratios `NUMERIC(18,10)` or `NUMERIC(9,6)`.

**Percentages are always stored as decimal fractions.** `0.008`, never `0.8` meaning
0.8%.

### 4. Tenancy and entitlements are enforced server-side, in exactly one place

- **One** base queryset / permission class that every view inherits. No view filters
  by client on its own.
- **PostgreSQL row-level security** as a second layer, including on reference tables
  (they hold client-created values, so they hold client data).
- **One** entitlement check everywhere: `has_entitlement(user, "FEATURE_CODE")`.
- Client-side route guards are UX only. Client-side rate limiting is not security.

### 5. Risk metrics: whole financial portfolio, never real estate

Metrics run on the **whole financial portfolio including free cash, livrets and
fonds euros**, treated as zero-volatility assets. The cash and guaranteed share is
**displayed beside every metric, non-optionally**.

**Never compute a Sharpe ratio over a portfolio containing real estate.** Property has
no price series, is illiquid and is leveraged.

---

## Never do these

- `FloatField`, or Python `float`, in the money path
- Literal strings in JSX — every label goes through `t()` (the lint rule fails the build)
- Money arithmetic in the browser — totals come from the API as strings
- A Stripe price ID anywhere except `Plan.stripe_price_id`
- Client filtering written by hand inside a view
- Frontier weight vectors crossing the API boundary
- SQLite, in any environment, including tests
- Enums with hardcoded display strings for any dimension — use a reference table
- Production credentials in a local `.env`

---

## Conventions

**Database** — `snake_case`; Django default table naming; `created_at` / `updated_at`
on every table; `deleted_at` soft delete where data must survive; all timestamps
timezone-aware UTC.

**Python** — `snake_case`, PEP 8, ruff, type hints on all public functions. Django apps
mirror the module list: `accounts`, `advisors`, `portfolio`, `instruments`, `reference`,
`fees`, `analytics`, `reports`, `imports`, `realestate`, `billing`.

**TypeScript** — `camelCase` variables, `PascalCase` components and types, one component
per file. Money is always a `string`.

**API** — versioned under `/api/v1/`, RESTful plural nouns, snake_case JSON from DRF,
converted to camelCase in one place at the frontend boundary.

**Feature codes** — SCREAMING_SNAKE: `DASHBOARD`, `RISK`, `REPORTS`, `REAL_ESTATE`,
`AUDIT_PDF`, `ADVISOR`.

**i18n keys** — `namespace:section.key` in dot case. Namespaces: `common`, `auth`,
`validation`, `portfolio`, `risk`, `realestate`, `reports`, `billing`.

**Git** — branches `type/short-description`; Conventional Commits with the Django app
or frontend module as the scope.

---

## These must have tests, without exception

Each fails silently and expensively.

| Area | Minimum cases |
|---|---|
| **Entitlement resolver** | free tier; active; trialing; expired; past_due; cancelled-in-period; valid grant; expired grant; revoked grant; subscription AND grant; metered limit |
| **Tenancy filtering** | own data visible; other client's invisible; advisor with active link; advisor with revoked link; **cross-tenant read fails at the database layer with the application filter deliberately removed** |
| **Transaction deduplication** | re-import identical file; overlapping ranges; same-day repeated trade; normalisation equivalence across parsers |
| **FX conversion** | weekend/holiday resolution; cross rate via EUR; identity rate; broker rate overriding reference; historical figure unchanged after a rate correction |
| **Fee calculations** | multi-currency; schedule change mid-period; TER change mid-period; accrual superseded by a real charge; **entry fees not annualised**; embedded fees not summed with cash fees |

Tests run against **real PostgreSQL**. Never SQLite — the constraints and RLS being
tested do not exist there.

---

## Repository layout (ADR-028)

```
backend/     Django + DRF. apps/ mirrors the module list.
frontend/    Next.js — marketing site and app in one.
contracts/   openapi.json + generated/api-types.ts. The boundary.
infra/       docker-compose.yml, render.yaml
docs/        adr/README.md — every decision, one line each
```

Generated feature-code types are a developer convenience, **never an authority** —
entitlements resolve against the database.

---

## Safety guards

1. **Beat runs only where enabled** — `ENABLE_BEAT=true` on the Render worker, nowhere else.
2. **Environment mismatch refuses to boot** — `ENVIRONMENT=local` plus a non-local
   database host raises on startup.
3. **Date-keyed lock on every scheduled task** — makes a double-fire harmless.

Celery Beat runs embedded in the single worker (`celery worker -B`) to stay inside the
€30/month budget. **If a second worker is ever added, Beat must move to its own service.**

---

## Where to look

- **Notion workspace** — the full specification, all reasoning
- **`docs/adr/README.md`** — every architectural decision, one line each
- Roadmap and Open Questions live in Notion databases; work one roadmap item per branch
