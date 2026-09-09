# Frontend — Next.js + TypeScript

Read the root `CLAUDE.md` first. This file adds frontend-specific rules.

## The two rules that fail the build

**1. No literal strings in JSX.** Every label goes through `t()` with a
`namespace:section.key`. The allowlist holds punctuation only — adding a word to it is
a conversation, not a quick fix.

**2. No money arithmetic.** JavaScript numbers are IEEE 754 doubles; the whole point of
`NUMERIC` in the database is lost the moment a total is summed in a component. Money
arrives from the API as a **string** and is formatted, never computed.

```ts
marketValueBase: string   // correct
marketValueBase: number   // defect
```

## Structure

- Marketing site and application live in the same app (SEO).
- `camelCase` variables and functions, `PascalCase` components and types.
- One component per file, named for the component.
- Hooks are `useThing`.
- The API client converts snake_case to camelCase in **one place**. Components never
  see snake_case.

## Every figure states its context

A number with no context will be misread. Each displayed figure carries, as applicable:

- its **currency** (no bare numbers)
- its **as-of date**
- whether any input was **estimated** (`is_estimated` propagates from opening balances)
- the active **look-through mode**, as a visible chip — not a tooltip
- for risk metrics, the **cash and guaranteed share**
- for coverage, the **scheme name and its verification date**

## Display rules

- `font-variant-numeric: tabular-nums` on every numeric cell, with the numeric font token.
- **Gain and loss are never signalled by colour alone** — always a sign or an arrow.
- **Text selection must work** in tables and on card values. Users copy ISINs and
  amounts constantly. Restrict `user-select: none` to genuine chrome.
- Headings are not automatically uppercased. Uppercase is for small labels and eyebrows.
- Exposure above a compensation ceiling renders `--neutral`, **never `--negative`** —
  it is a fact, not a fault.
- Custom (client-created) reference values carry a small "custom" affordance.

## Entitlements

`useEntitlements().has("RISK")` for UX only. **The API is the access control.** Never
re-derive entitlements from plan or price data in the browser.

## i18n

- Keys are English, descriptive and stable. Never the French string, never the display
  string.
- Client-created labels are the one exception: resolve as `label ?? t(translation_key)`,
  displayed exactly as the user typed them, never translated.
- Both catalogues change together — CI fails when a key exists in one and not the other.
- Number and date formatting follows `locale`, not `language`. `Intl.NumberFormat(locale, …)`.

## Three states, always

Every module needs **empty**, **locked** and **computing** designed, not just the happy
path. The locked state must say plainly that **the user's data is safe and still there**.

## Language

No advice, anywhere — including chart labels, empty states and marketing copy.
"63% of your assets are capital-guaranteed" is a fact. "You are holding too much cash"
is forbidden.
