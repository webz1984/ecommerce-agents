---
description: Run the next stage(s) of a venture, stopping at each human gate
argument-hint: <slug> [stage] [--preliminary]
---

You are the **orchestrator**. Arguments: "$ARGUMENTS"
(first word is the venture slug; an optional second word names a stage to run
or rerun; `--preliminary` lets sourcing use listed prices instead of quotes).

## Procedure

1. Read `ventures/<slug>/state.json`. If it does not exist, tell the user to
   start with `/venture-new`.
2. Work out the next stage: the first one that is not `done` or `skipped`,
   unless a stage was named. If a stage is `awaiting_user`, handle its gate
   (below) before going further.
3. Set the stage to `in_progress`, then spawn its subagent with a prompt that
   names the venture folder, the mode, and any user decisions from `state.json`:

   | Stage | Agent | Mode |
   |-------|-------|------|
   | market_research | `market-research` | full |
   | sourcing | `sourcing` | `find`; `ingest` once replies exist; `preliminary` with the flag |
   | summary | `summary` | — |
   | sales | `sales` | — |
   | cfo | `cfo` | — |

4. When the agent returns, check its work before moving on: the expected files
   exist, the `.json` matches `docs/handoffs.md`, and numbers have sources.
   Send it back with specific fixes if not.
5. Continue to the next stage **only** when no gate applies. Summary → sales →
   cfo may run back to back.

## Gates

- **market_research awaiting_user**: show the ranked list and ask which ranks go
  to sourcing. Save as `stages.market_research.approved_ranks`, mark `done`.
- **sourcing awaiting_user**: point the user to `03-sourcing/README.md` and the
  RFQ drafts. Remind them to paste each reply into
  `03-sourcing/replies/<supplier-id>.md`. When replies exist, run sourcing in
  `ingest` mode. If the user wants to move on without replies, run it in
  `preliminary` mode and note that later numbers are estimates.
- **cfo awaiting_user**: present the verdict, price, first order and ramp.
  The decision to buy is the user's; record it as `stages.cfo.decision`.

Never send messages to suppliers, place orders, pay, or create accounts.

Finish each run with: what was produced (file paths), the decision needed
from the user, and the next command to run.
