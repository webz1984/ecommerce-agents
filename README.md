# ecommerce-agents

A Claude Code agent team that takes a product from idea to a sourced, priced,
ready-to-list launch plan.

```
/venture-new ──► brainstorm (you + Claude, several rounds, quick market checks)
                    │  you pick 1–3 ideas
                    ▼
/venture-run ──► market-research ──► ranked, evidence-backed list
                    │  you pick what to source
                    ▼
                 sourcing ──► supplier shortlist + RFQ drafts (EN / 中文)
                    │  you send RFQs, paste replies into 03-sourcing/replies/
                    ▼
                 sourcing (ingest) ──► comparable quotes, supplier pick
                    ▼
                 summary ──► go / no-go report + next steps
                    ▼
                 sales ──► channel plan, name, listings, image & packaging briefs
                    ▼
                 cfo ──► landed cost, price, first order, ramp plan (3 scenarios)
                    │  you decide whether to buy
```

## Setup

1. Clone and open the folder in Claude Code:
   `git clone https://github.com/webz1984/ecommerce-agents && cd ecommerce-agents && claude`
2. Give the research agents a browser. Amazon, Walmart and 1688 block plain
   page fetches, so the agents work far better with one:
   - **Claude in Chrome** (uses your own browser): start with `claude --chrome`, or
   - **Playwright MCP** (bundled in `.mcp.json`, needs Node.js): approve it the
     first time Claude Code asks.
3. Edit `config/assumptions.yaml`: your cash budget, margin target, market.

## Use

| Command | What it does |
|---|---|
| `/venture-new [idea]` | Brainstorm with you and create `ventures/<slug>/` |
| `/venture-run <slug>` | Run the next stage(s) until a decision is needed |
| `/venture-run <slug> <stage>` | Rerun one stage (e.g. `sales`) |
| `/venture-run <slug> --preliminary` | Move past sourcing on listed prices before quotes arrive |
| `/venture-status [slug]` | What's done and what's waiting on you |

All outputs land in `ventures/<slug>/`, numbered by stage, each with a readable
`.md` report and a `.json` handoff (see `docs/handoffs.md`).

## What's in here

```
CLAUDE.md                     orchestrator rules, gates, evidence standards
.claude/agents/               market-research, sourcing, summary, sales, cfo
.claude/commands/             venture-new (brainstorm), venture-run, venture-status
docs/handoffs.md              JSON shape passed between stages
config/assumptions.yaml       your defaults + links to verify fees/duties
tools/unit_economics.py       CFO math: landed cost, fees, pricing, MOQ, ramp, scenarios
tools/sample_model.json       example model (illustrative numbers)
templates/state.json          per-venture stage tracker
```

### CFO calculator on its own

```bash
python3 tools/unit_economics.py tools/sample_model.json              # base, pessimistic, optimistic
python3 tools/unit_economics.py --quick --price 19.99 --unit-cost 1.6 \
  --freight-per-unit 0.8 --fee-pct 15 --fulfilment 4.2 --duty-pct 28  # rough margin check
```

## Guardrails built in

- Agents never contact suppliers, place orders, pay, or sign up for anything.
  They draft; you send and decide.
- Every number carries a source and date; estimates are labelled.
- Fees, freight and tariffs are looked up at run time (tariffs on Chinese
  goods have changed often), not taken from memory.
- Name checks are a quick screen, not trademark clearance. Get proper advice
  before you commit to a brand.
- Browsing reads pages like a person would: no logins on your behalf, no
  CAPTCHA solving, no bulk scraping.

## Limits

- Sales estimates come from public signals (BSR, "bought in past month",
  review velocity). Connect a tool like Jungle Scout, Helium 10 or Keepa for
  better numbers.
- The sales agent writes image briefs, prompts and SVG starter mockups; real
  product photos still need samples and a photographer or image tool.
