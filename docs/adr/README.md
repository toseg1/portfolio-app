# Architecture Decision Records

Every decision below is **made**. Do not re-open them, do not offer alternatives, and
do not work around them. If a decision genuinely needs revisiting, that is a
conversation with the project owner, not a code change.

Full reasoning for each lives in the Notion database. This file is the in-repo index so
the "why" is answerable without leaving the editor.

**Notion:** [02 — Architecture Decision Records](https://app.notion.com/p/f3bdf882d2dd4db2a43e31f2f613ffcd)

---

## Data model

| # | Decision | Notion |
|---|---|---|
| 001 | **PostgreSQL with `NUMERIC` for all money.** Never SQLite, never floats, in any environment including tests. | [link](https://app.notion.com/p/3d58804e7816815fb31fcf85617e08df) |
| 002 | **Transactions are the source of truth; positions are derived.** Transaction rows immutable; no mutable "current quantity" anywhere. | [link](https://app.notion.com/p/3d58804e7816812e9d2debc1886e4a7e) |
| 003 | **Never convert currency on write.** Transaction currency + trade-date FX rate frozen on the row + portfolio base currency, as three facts. | [link](https://app.notion.com/p/3d58804e781681f580b8d831ca5bb5dd) |
| 004 | **Reference data as FK tables with translation keys**, never enums with hardcoded strings. | [link](https://app.notion.com/p/3d58804e781681509eb8f318846e6f21) |
| 005 | **`Portfolio` is a real table with a 1:1 constraint in v1.** Accounts never hang off `Client`. Dropping the unique index is the whole future migration. | [link](https://app.notion.com/p/3d58804e78168124b239d4359aa7fe66) |
| 006 | **Deterministic `external_id` hash for import deduplication, built in v1.** Retrofitting it onto dirty data is unresolvable. | [link](https://app.notion.com/p/3d58804e7816810e87f5dcbf46d91742) |
| 023 | **Crypto is modelled identically to every other asset class.** Distinction carried by `asset_class` and `custody_type`, not a separate subsystem. | [link](https://app.notion.com/p/3d58804e7816813e9537e962aeba5cd6) |
| 025 | **Every dimension is client-extensible** — users create their own reference values. Client rows carry no behaviour. **`Currency` is the one exclusion.** | [link](https://app.notion.com/p/3d58804e781681a49d5fc9a29c66fe83) |
| 026 | **`Institution` is a first-class entity** carrying deposit, securities and insurance guarantee scheme membership. Coverage is per client, per legal entity, per category. | [link](https://app.notion.com/p/3d58804e78168100955bd93256bb1dbf) |

## Backend and analytics

| # | Decision | Notion |
|---|---|---|
| 007 | **Celery Beat for scheduling. Airflow explicitly rejected** — three extra services and ~€20/month to run one daily job. Revisit with Dagster, not Airflow. | [link](https://app.notion.com/p/3d58804e7816815da49bf5bf295ff7de) |
| 008 | **Quantitative work runs in Celery tasks** with pandas/numpy and PyPortfolioOpt or riskfolio-lib. Frontier weights are dropped inside the task. | [link](https://app.notion.com/p/3d58804e781681a68481d12a1990c4a0) |
| 027 | **Risk metrics include cash and capital-guaranteed holdings**, treated as zero-volatility assets. The cash share is disclosed beside every metric. No second competing Sharpe. Real estate stays excluded. | [link](https://app.notion.com/p/3d58804e781681919d46d2a5f6fb72e3) |

## Reporting

| # | Decision | Notion |
|---|---|---|
| 009 | **PDF rendering runs in a Celery worker**, never in the web process. | [link](https://app.notion.com/p/3d58804e781681c8a418e4cdc9c5fea7) |
| 010 | **Reports are JSONB snapshots re-rendered on download**, not stored PDFs. Exceptions: the free-audit PDF and anything a client signs. | [link](https://app.notion.com/p/3d58804e781681ec8298ee646411d204) |

## Auth and security

| # | Decision | Notion |
|---|---|---|
| 011 | **Session auth via httpOnly cookies with django-allauth. Explicitly not JWTs in browser storage** — any XSS would become full account takeover on net-worth data. | [link](https://app.notion.com/p/3d58804e78168103be39fbaecaf35e86) |
| 012 | **Advisor viewing a client is an impersonation context, not a third role.** Link revalidated every request; audit row on entry; persistent banner. | [link](https://app.notion.com/p/3d58804e7816819bb788fbae6cbebfb1) |
| 022 | **Tenancy enforced in exactly one place**, backed by PostgreSQL row-level security as a second layer. | [link](https://app.notion.com/p/3d58804e78168125a838eb90f8df3777) |

## Frontend

| # | Decision | Notion |
|---|---|---|
| 016 | **Next.js + TypeScript, marketing site in the same app** to capture SEO. | [link](https://app.notion.com/p/3d58804e7816810ea0f4c020dc77526c) |
| 017 | **Charting library — Recharts vs ECharts. STATUS: PROPOSED, NOT DECIDED.** Must be settled before the Risk & Analytics module. | [link](https://app.notion.com/p/3d58804e781681af9af7edadebee0c3b) |
| 024 | **French and English at launch with react-i18next namespaces.** i18n is not retrofitted; a lint rule bans literal strings in JSX from day one. | [link](https://app.notion.com/p/3d58804e781681eb9a04c32dac47693e) |

## Hosting and operations

| # | Decision | Notion |
|---|---|---|
| 013 | **Render, EU region (Frankfurt), hard €30/month ceiling.** No headroom for a staging environment. | [link](https://app.notion.com/p/3d58804e78168194953bf45c4547be4b) |
| 014 | **Containerise from day one** so a Hetzner VPS migration is a weekend. Trigger: needing staging, or Postgres outgrowing Basic. | [link](https://app.notion.com/p/3d58804e7816816ba867ed2629b88cbb) |
| 015 | **Object storage on Cloudflare R2 or Scaleway (EU)** via the S3 API. Render provides none. | [link](https://app.notion.com/p/3d58804e781681fd8f85ee8e8b25bdbe) |
| 028 | **One monorepo for backend and frontend**, with an explicit `contracts/` boundary. Includes the three local/production safety guards. | [link](https://app.notion.com/p/3d58804e781681f2b3acf7712e34e565) |

## Data sources

| # | Decision | Notion |
|---|---|---|
| 018 | **All market data behind a provider abstraction.** Scraped sources are not licensed for commercial redistribution and IP bans would break the product. Revisit at the first paying customer. | [link](https://app.notion.com/p/3d58804e78168138b911e85376165adc) |
| 019 | **Broker parser registry — one parser per broker, one canonical schema.** No universal template. PDF statements out of scope for v1. | [link](https://app.notion.com/p/3d58804e7816815bb740d29d048d0fa5) |

## Billing

| # | Decision | Notion |
|---|---|---|
| 020 | **Entitlements are data.** Never gate a feature on a Stripe price ID. One check everywhere, enforced server-side. | [link](https://app.notion.com/p/3d58804e7816816e8d66c48638a96f61) |
| 021 | **Comped access uses `EntitlementGrant`** — never 100%-off Stripe subscriptions, which pollute MRR and complicate webhooks. | [link](https://app.notion.com/p/3d58804e78168173ac72d8541b4c47d8) |

---

## Still open — do not resolve these in code

The full list is the Open Questions database in Notion. The two that can block work:

- **ADR-017 — charting library.** Decide before building Risk & Analytics.
- **Legal confirmation of the Tier 1 boundary** — the efficient frontier as a reference
  curve rather than a target. Owner: the project owner, with a regulatory lawyer.
  Needed before the risk module reaches a paying customer.
