# Handoff formats

Each stage writes a `.json` handoff for the next stage. Fields marked `?` are
optional. Every `source` is `{ "url": "...", "seen": "YYYY-MM-DD" }`.

## 01-brainstorm.json

```json
{
  "venture": "slug",
  "founder_profile": {
    "budget_usd": 5000,
    "time_per_week_hours": 10,
    "location": "US",
    "target_markets": ["US"],
    "experience": "first product",
    "constraints": ["no batteries", "ships in a small box"],
    "interests": ["outdoor", "pets"]
  },
  "selected_ideas": [
    {
      "id": "idea-1",
      "name": "Collapsible silicone dog bowl with clip",
      "customer": "hikers with dogs",
      "problem": "bowls are bulky and fall off packs",
      "angle": "what makes ours different",
      "search_terms": ["collapsible dog bowl", "travel dog bowl"],
      "why_picked": "user's words"
    }
  ],
  "rejected_ideas?": [{ "name": "...", "reason": "..." }]
}
```

## 02-market-research.json

```json
{
  "venture": "slug",
  "ranked": [
    {
      "rank": 1,
      "idea_id": "idea-1",
      "product": "specific product spec to source",
      "score": 78,
      "scores": { "demand": 8, "trend": 7, "competition": 6, "margin_room": 8,
                  "differentiation": 7, "logistics": 9, "compliance": 9 },
      "price_band_usd": { "low": 14.99, "typical": 19.99, "high": 29.99 },
      "demand_evidence": [{ "claim": "...", "source": {} }],
      "top_competitors": [
        { "title": "...", "channel": "amazon", "price": 19.99, "rating": 4.4,
          "reviews": 3200, "est_monthly_units?": 1500, "source": {} }
      ],
      "customer_complaints": ["clip breaks", "smells like rubber"],
      "customer_loves": ["packs flat"],
      "differentiation_ideas": ["metal carabiner", "food-grade platinum silicone"],
      "must_have_specs": ["food-grade silicone", "≥ 600 ml"],
      "risks": ["crowded on Amazon", "seasonal peak in summer"]
    }
  ],
  "not_recommended?": [{ "idea_id": "...", "reason": "..." }]
}
```

## 03-sourcing/sourcing.json

```json
{
  "venture": "slug",
  "status": "rfq_drafted | quotes_received | complete",
  "products": [
    {
      "product_rank": 1,
      "spec_sheet": "03-sourcing/spec-rank1.md",
      "suppliers": [
        {
          "id": "sup-1",
          "name": "Shenzhen Example Co.",
          "platform": "alibaba | 1688 | aliexpress | made-in-china | globalsources | other",
          "url": "...",
          "type": "manufacturer | trading company | unknown",
          "years_on_platform?": 6,
          "verified?": true,
          "listed_price_range?": "1.20–1.80 USD",
          "listed_moq?": 500,
          "rfq_draft": "03-sourcing/rfq/sup-1.md",
          "quote?": {
            "unit_price_usd": [{ "qty": 500, "price": 1.55 }, { "qty": 2000, "price": 1.25 }],
            "moq": 500,
            "sample_cost_usd": 40,
            "production_lead_days": 20,
            "incoterm": "EXW | FOB | DDP",
            "packaging": "opp bag, custom box +0.15",
            "carton": { "units": 100, "kg": 12, "cm": [50, 40, 35] },
            "certs": ["LFGB"],
            "notes": "..."
          },
          "red_flags": []
        }
      ],
      "recommended_supplier?": "sup-1"
    }
  ]
}
```

## 04-summary.json

```json
{
  "venture": "slug",
  "go_recommendation": "go | go-with-conditions | no-go",
  "lead_product": { "product_rank": 1, "supplier": "sup-1" },
  "key_facts": { "price_band_usd": {}, "unit_cost_usd": 1.25, "moq": 500 },
  "open_questions": ["..."],
  "next_steps": ["order 3 samples", "..."]
}
```

## 05-sales/sales.json

```json
{
  "venture": "slug",
  "channels": [
    { "channel": "amazon_fba", "role": "primary | secondary | test", "why": "..." }
  ],
  "product_name": "...",
  "positioning": "...",
  "listings": { "amazon_fba": "05-sales/listing-amazon.md" },
  "creative_briefs": "05-sales/creative/",
  "launch_marketing": [{ "tactic": "...", "est_monthly_budget_usd": 500 }]
}
```

## 06-cfo outputs

- `06-cfo/model.json`: inputs for `tools/unit_economics.py` (see `tools/sample_model.json`).
- `06-cfo/results.json`: the script's output.
- `06-cfo.md`: the human report.
