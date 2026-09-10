# Backend — Django + DRF

Read the root `CLAUDE.md` first. This file adds backend-specific rules.

## App boundaries

Apps mirror the module list. Do not create apps outside this set without asking.

```
config/        settings, urls, celery app
accounts/      User (email-only, no username), auth (allauth/axes/admin-MFA
               wiring) — roadmap item 1. Client/Profile land with later items.
advisors/      AdvisorLink, AccessAuditLog, impersonation context
portfolio/     Portfolio, Account, Transaction, position derivation
instruments/   Instrument, PriceHistory, EtfHolding, IsinTickerMapping, FxRate
reference/     every reference/dimension table
fees/          TransactionFee, RecurringAccountFee, InstrumentFeeProfile
analytics/     risk metrics, frontier, look-through aggregation
reports/       ReportRun, StoredDocument, PDF templates
imports/       broker_parsers registry, ImportBatch
realestate/    Property, Unit, Lease, Loan, CashflowEntry, Valuation, Liability
billing/       Feature, Plan, Subscription, EntitlementGrant, StripeEvent
notifications/ EmailLog, SuppressionList, NotificationPreference, sending (ADR-029)
```

`notifications` sits outside the product module list above — it's infrastructure the
other modules call into (roadmap item 1.5), added by asking first since it wasn't in
the original set.

## Money

- `DecimalField` only. **`FloatField` is a defect.**
- `Decimal` in, `Decimal` out of every public function in the money path.
- The float boundary in analytics is **explicit and one-directional**: values leave the
  database as `Decimal`, are cast to float *inside* the Celery task, and anything
  returning as money is cast back. Ratios and statistics may stay float — they are
  measurements, not money.
- Every monetary column is paired with an explicit currency column.

## Tenancy

Every view inherits the single base queryset / permission class. It resolves the
effective client — the user's own, or the impersonated client after validating the
`AdvisorLink` on **this** request — and filters on it.

- A view that needs to bypass it does not exist. If one appears to, raise it; do not
  work around it.
- The RLS session variable is set per request **and per Celery task**, and reset after.
- Cross-client jobs (daily prices, backups) run as a role explicitly and narrowly
  exempt from RLS — never the application role.

## Reference tables are client-extensible

Every dimension carries `client_id` (NULL = system), `label` (client rows) or
`translation_key` (system rows), `is_system`, `created_by_user_id`.

- **Client rows carry no behaviour.** Caps, eligibility rules, vendor mappings and
  look-through eligibility are NULL or false.
- **Any code branching on a `code` must check `is_system` first.** A custom envelope a
  user names `PEA` must never trigger the PEA eligibility rule.
- `Currency` is the one non-extensible dimension. Enforce it in the model layer.

## Celery

- All quantitative work and all PDF rendering runs in tasks, never in the web process.
- Every scheduled task is **idempotent per date** — upserts keyed on the natural key,
  never blind inserts. Assume it will be re-run, because after a failure it will be.
- Wrap Beat-scheduled tasks in the date-keyed lock.
- Beat runs embedded in the single worker. Guard 1 refuses `--beat` without
  `ENABLE_BEAT=true`.

## Email

Sender-role settings (`EMAIL_DOMAIN`, `EMAIL_FROM_SYSTEM`, `EMAIL_FROM_ADVISORY`,
`EMAIL_REPLY_TO`, `EMAIL_OPERATOR_ALERTS`) and guard 4 live in `config/settings.py`.
`EMAIL_BACKEND` points at Mailpit locally (`infra/docker-compose.yml`).

The `notifications` app (roadmap item 1.5, ADR-029) is the email module: `EmailLog`,
`SuppressionList`, `NotificationPreference` (04.8), sender-role resolution
(`senders.py`), the queueing entry point (`services.queue_email`) and the Celery send
path with retry/backoff and a suppression-list check (`tasks.py`). Callers never touch
SMTP or the suppression list directly — call `queue_email(...)`.

`EmailLog.user` / `NotificationPreference.user` are real `ForeignKey(accounts.User)`
now (roadmap item 1). `EmailLog.client_id` stays a plain column — `accounts.Client`
doesn't exist yet. Add that real FK + migration once it does.

`apps.accounts.adapters.AccountAdapter` (`ACCOUNT_ADAPTER`) is the concrete example
of "callers never touch SMTP directly": every allauth email (signup confirmation,
password reset, account-already-exists) is intercepted and routed through
`queue_email(...)`, using templates under
`notifications/templates/notifications/emails/auth.*/`.

Remaining v1 templates (advisor invitation, etc.) don't exist yet — each lands with
the feature that triggers it, extending `notifications/email_base.html` / `.txt`.

## Market data

Business logic depends on the `MarketDataProvider` interface. **Never import `yfinance`
or `stockdex` outside an adapter.** Rate limiting, retry and caching live in the
adapter layer.

## API

- Versioned under `/api/v1/`, snake_case JSON.
- Errors return `{detail, code, field_errors}` — `code` is translatable.
  **The API never returns a user-facing sentence.**
  - Exception: `/api/v1/auth/*` and `/api/v1/account/*` are django-allauth's own
    `allauth.headless` views (ADR-011) — they return allauth's own
    `{status, data, meta, errors}` envelope, not this shape. Deliberate,
    scoped to those two prefixes — do not reshape it.
- Advisor context: the viewed client id arrives on every request and is validated
  every time.

## Testing

`pytest` + `pytest-django`, factories over fixtures, **real PostgreSQL always**.
Broker parsers are tested against real anonymised export files committed as fixtures.
The five mandatory-test areas in the root `CLAUDE.md` are not optional.
