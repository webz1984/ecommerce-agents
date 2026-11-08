---
description: Show where each venture stands and what's waiting on you
argument-hint: [slug]
---

Arguments: "$ARGUMENTS"

Read `ventures/*/state.json` (or only the named slug). For each venture, show one
compact table row: slug, current stage, status, what it's waiting for, and the
next command to run. If a slug was given, also list the files each finished
stage produced and the headline from its report (verdict, top-ranked product,
recommended supplier, price and margin).
