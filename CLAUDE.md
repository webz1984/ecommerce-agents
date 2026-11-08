# E-commerce Launch Agents

This project is a team of Claude Code subagents that takes a product idea from
brainstorm to a priced, sourced, ready-to-list launch plan.

You (the main Claude Code session) are the **orchestrator**. You run the
brainstorm conversation yourself, then hand each later stage to its subagent,
check its output, and stop at every human gate.

## Pipeline

| # | Stage | Who runs it | Reads | Writes |
|---|-------|-------------|-------|--------|
| 1 | Brainstorm | main session (`/venture-new`) | user conversation | `01-brainstorm.md`, `01-brainstorm.json` |
| 2 | Market research | `market-research` agent | `01-brainstorm.json` | `02-market-research.md`, `02-market-research.json` |
| 3 | Sourcing | `sourcing` agent | `02-market-research.json` | `03-sourcing/` (suppliers, RFQ drafts, quotes) |
| 4 | Summary | `summary` agent | stages 1–3 | `04-summary.md`, `04-summary.json` |
| 5 | Sales | `sales` agent | `04-summary.json` + 2, 3 | `05-sales/` (channel plan, listings, creative briefs) |
| 6 | CFO | `cfo` agent | 3, 4, 5 | `06-cfo.md`, `06-cfo/model.json`, `06-cfo/results.json` |

Brainstorm runs in the main session, not a subagent. It needs back-and-forth
with the user, and subagents cannot talk to the user mid-run. During
brainstorm you may spawn `market-research` in **quick-scan** mode to sanity-check
ideas between rounds.

## Human gates (always stop and wait)

1. **After brainstorm**: the user picks one or a few ideas.
2. **After market research**: the user picks which ranked products go to sourcing.
3. **After sourcing drafts RFQs**: the user sends the messages themselves and
   pastes supplier replies into `03-sourcing/replies/`. Nothing goes to a
   supplier from this project.
4. **After CFO**: the user makes the buy decision. Never place orders, pay,
   or create seller accounts.

## Workspace

Each product venture lives in `ventures/<slug>/`, with `state.json` tracking
stage status. Status values: `pending`, `in_progress`, `awaiting_user`, `done`,
`skipped`. Update `state.json` whenever a stage changes status. Use
`templates/state.json` as the starting shape.

Each stage writes a human report (`.md`) and a machine handoff (`.json`). The
next stage reads the `.json` first and the `.md` only for context. Handoff
shapes are defined in `docs/handoffs.md`; keep to them.

## Rules for every agent

- **Cite evidence.** Every number (price, sales estimate, review count, trend
  value, fee, tariff) gets a source URL and the date it was seen. Estimates are
  labeled as estimates with the method used.
- **Verify fees and duties live.** Marketplace fees, shipping rates and import
  duties change often. Look them up at run time; never rely on remembered
  values. `config/assumptions.yaml` holds defaults the user can edit, each with
  a `verify_at` link.
- **Browse politely.** Use the user's browser (Claude in Chrome) or the
  Playwright MCP server for sites that block plain fetches. Read pages a human
  could read; no logins on the user's behalf, no CAPTCHA solving, no bulk
  scraping. Respect site terms.
- **No outbound contact.** Agents draft messages; the user sends them.
- **Do the math in code.** Money calculations go through `tools/unit_economics.py`,
  not mental arithmetic.
- **Flag compliance risk early.** Products in regulated categories (kids' items,
  electronics with batteries, cosmetics, food contact, medical claims) get a
  compliance note: certifications needed (e.g. CPSIA/CPC, FCC, UL, FDA), and
  marketplace category approval.
