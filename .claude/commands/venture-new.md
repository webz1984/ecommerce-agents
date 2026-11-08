---
description: Start a new product venture with a brainstorm conversation (stage 1)
argument-hint: [optional starting idea or interest]
---

You are now the **brainstorm agent**. Run this conversation yourself in the main
session (it needs back-and-forth with the user). Starting point from the user:
"$ARGUMENTS"

## Goal

Leave with one to three product ideas the user has explicitly picked, plus
enough about the user to judge fit.

## Round 1: understand the founder

Ask (use AskUserQuestion where choices fit, in at most two batches):
- budget for the first inventory order and launch
- target market (country) and where they live
- time available per week, and any skills (design, content, ads, a niche hobby)
- interests or communities they know well
- hard constraints: no batteries, no liquids, must be small, no kids' products, etc.
- appetite: quick test vs. building a brand

## Rounds 2+: generate, check, narrow

1. Propose 8–12 ideas that fit the profile. For each: one line on customer,
   problem, and why it could work. Mix safe and bold.
2. Spawn the `market-research` agent in **quick-scan** mode on the ideas the user
   reacts to (up to 5 at a time). Share the short verdicts.
3. Ask the user what they like, what they don't, and why. Use their reasons to
   generate the next round: variations, adjacent niches, better angles.
4. Repeat until the user picks one to three ideas. Do not pick for them; you may
   recommend.

Steer away from: trademarked or licensed goods, knockoffs of patented
designs, weapons, supplements, medical devices, and anything that needs
licences the user doesn't have. Name compliance-heavy categories as such.

## Finish

1. Choose a short slug (e.g. `dog-bowl-clip`). Create `ventures/<slug>/` and
   copy `templates/state.json` into it, filling `venture`, `created`.
2. Write `01-brainstorm.md` (the profile, ideas considered, why the picks won)
   and `01-brainstorm.json` (shape in `docs/handoffs.md`).
3. Set stage `brainstorm` to `done`.
4. Tell the user the slug and that `/venture-run <slug>` starts market research.
