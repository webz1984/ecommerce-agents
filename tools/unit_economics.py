#!/usr/bin/env python3
"""Unit economics, pricing, order sizing and ramp plan for a sourced product.

Full model:
    python3 tools/unit_economics.py path/to/model.json [--scenario base|pessimistic|optimistic|all]
                                                       [--out results.json]
Quick margin check (used by the summary stage):
    python3 tools/unit_economics.py --quick --price 24.99 --unit-cost 2.10 \
        --freight-per-unit 0.80 --fee-pct 15 --fulfilment 4.50 [--duty-pct 25] [--tacos-pct 15]

Standard library only. All money is in the model's currency (USD by default).
See tools/sample_model.json for the input shape.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys

DEFAULT_SCENARIOS = {
    "base": {},
    "pessimistic": {"freight_x": 1.3, "ads_x": 1.5, "price_x": 0.9, "returns_x": 2.0},
    "optimistic": {"freight_x": 0.9, "ads_x": 0.8, "price_x": 1.0, "returns_x": 0.75},
}


def r2(x: float) -> float:
    return round(x + 0.0, 2)


# ---------------------------------------------------------------- inputs

def apply_scenario(model: dict, name: str) -> dict:
    m = copy.deepcopy(model)
    s = {**DEFAULT_SCENARIOS.get(name, {}), **model.get("scenarios", {}).get(name, {})}
    fx, ax, px, rx = (s.get(k, 1.0) for k in ("freight_x", "ads_x", "price_x", "returns_x"))
    fr = m["freight"]
    for k in ("rate_per_cbm", "rate_per_kg", "min_charge", "inbound_per_unit"):
        if fr.get(k) is not None:
            fr[k] *= fx
    m["marketing"]["steady_tacos_pct"] *= ax
    for ph in m["marketing"]["phases"]:
        ph["ad_spend_per_day"] *= ax
        ph["price"] *= px
    m["pricing"]["candidates"] = [p * px for p in m["pricing"]["candidates"]]
    m["returns"]["rate_pct"] *= rx
    m["_scenario"] = {"name": name, **s}
    return m


def unit_price_at(tiers: list[dict], qty: int) -> tuple[float, bool]:
    """Price for qty from tiers [{qty, price}]; second value True if qty is below the lowest tier."""
    tiers = sorted(tiers, key=lambda t: t["qty"])
    below = qty < tiers[0]["qty"]
    price = tiers[0]["price"]
    for t in tiers:
        if qty >= t["qty"]:
            price = t["price"]
    return price, below


# ------------------------------------------------------------- landed cost

def landed_cost(m: dict, qty: int) -> dict:
    sup, carton, fr, duty = m["supplier"], m["carton"], m["freight"], m["duty"]
    unit, below_moq = unit_price_at(sup["tiers"], qty)
    goods_unit = unit + sup.get("packaging_per_unit", 0) + sup.get("labeling_per_unit", 0)
    goods = goods_unit * qty
    one_time = sup.get("tooling_one_time", 0)

    cartons = math.ceil(qty / carton["units"])
    kg = cartons * carton["gross_kg"]
    l, w, h = carton["dims_cm"]
    cbm = cartons * l * w * h / 1_000_000
    mode = fr.get("mode", "sea")
    if mode == "sea":
        freight_main = max(cbm * fr["rate_per_cbm"], fr.get("min_charge", 0))
    else:  # air / express: chargeable weight is the larger of actual and volumetric
        vol_kg = cbm * fr.get("volumetric_kg_per_cbm", 167)
        freight_main = max(max(kg, vol_kg) * fr["rate_per_kg"], fr.get("min_charge", 0))
    freight = freight_main + fr.get("origin_fees", 0) + fr.get("destination_fees", 0)
    inbound = fr.get("inbound_per_unit", 0) * qty

    customs_value = goods if sup.get("incoterm", "FOB") != "EXW" else goods + fr.get("origin_fees", 0)
    duty_rate = (duty.get("duty_pct", 0) + duty.get("extra_tariff_pct", 0)) / 100
    duties = customs_value * duty_rate
    mpf = customs_value * duty.get("mpf_pct", 0) / 100
    if duty.get("mpf_min") is not None:
        mpf = max(mpf, duty["mpf_min"])
    if duty.get("mpf_max") is not None:
        mpf = min(mpf, duty["mpf_max"])
    hmf = customs_value * duty.get("hmf_pct", 0) / 100 if mode == "sea" else 0
    broker = duty.get("broker_per_shipment", 0) + duty.get("bond_per_shipment", 0)
    import_total = duties + mpf + hmf + broker

    total = goods + one_time + freight + inbound + import_total
    return {
        "qty": qty,
        "below_moq": below_moq or qty < sup.get("moq", 0),
        "unit_price": r2(unit),
        "cartons": cartons,
        "kg": r2(kg),
        "cbm": round(cbm, 3),
        "total": r2(total),
        "per_unit": {
            "goods": r2(goods_unit),
            "tooling": r2(one_time / qty),
            "freight": r2(freight / qty),
            "inbound": r2(inbound / qty),
            "duty_and_import_fees": r2(import_total / qty),
            "landed": r2(total / qty),
        },
    }


# ----------------------------------------------------------- per-sale P&L

def channel_pcts(m: dict) -> float:
    ch = m["channel"]
    return (ch.get("referral_pct", 0) + ch.get("payment_pct", 0)) / 100


def sale_economics(m: dict, price: float, landed: float, tacos_pct: float | None = None) -> dict:
    ch, ret = m["channel"], m["returns"]
    tacos = m["marketing"]["steady_tacos_pct"] if tacos_pct is None else tacos_pct
    referral = max(price * ch.get("referral_pct", 0) / 100, ch.get("referral_min", 0))
    payment = price * ch.get("payment_pct", 0) / 100 + ch.get("payment_fixed", 0)
    fulfil = ch.get("fulfilment_per_unit", 0)
    storage = ch.get("storage_per_unit_month", 0) * ch.get("avg_months_stored", 0)
    other = ch.get("other_per_unit", 0)
    rate = ret.get("rate_pct", 0) / 100
    returns = rate * (ret.get("unsellable_share_pct", 0) / 100 * landed
                      + ret.get("processing_per_return", 0))
    ads = price * tacos / 100
    channel_total = referral + payment + fulfil + storage + other
    contribution = price - landed - channel_total - returns
    net = contribution - ads
    return {
        "price": r2(price),
        "landed": r2(landed),
        "referral": r2(referral),
        "payment": r2(payment),
        "fulfilment": r2(fulfil),
        "storage": r2(storage),
        "other_channel": r2(other),
        "returns": r2(returns),
        "ads": r2(ads),
        "contribution_before_ads": r2(contribution),
        "net_profit": r2(net),
        "net_margin_pct": r2(100 * net / price) if price else None,
        "roi_pct": r2(100 * net / landed) if landed else None,
    }


def price_for_margin(m: dict, landed: float, margin_pct: float) -> float | None:
    """Lowest price reaching margin_pct net margin, assuming the % referral fee applies (not the minimum)."""
    ch, ret = m["channel"], m["returns"]
    fixed = (landed + ch.get("payment_fixed", 0) + ch.get("fulfilment_per_unit", 0)
             + ch.get("storage_per_unit_month", 0) * ch.get("avg_months_stored", 0)
             + ch.get("other_per_unit", 0)
             + ret.get("rate_pct", 0) / 100 * (ret.get("unsellable_share_pct", 0) / 100 * landed
                                                + ret.get("processing_per_return", 0)))
    denom = 1 - channel_pcts(m) - m["marketing"]["steady_tacos_pct"] / 100 - margin_pct / 100
    if denom <= 0:
        return None
    return r2(fixed / denom)


# ------------------------------------------------------ orders and ramp

def plan(m: dict) -> dict:
    sup, mk, inv, cash = m["supplier"], m["marketing"], m.get("inventory", {}), m.get("cash", {})
    phases = mk["phases"]
    steady_per_day = m["demand"]["steady_units_per_day"]
    safety_days = inv.get("safety_stock_days", 21)
    transit = m["freight"].get("transit_days", 35)
    lead = sup.get("production_lead_days", 25)
    samples = sup.get("sample_cost", 0) * sup.get("sample_count", 1)

    # First order covers the pre-scale phases plus safety stock at the last pre-scale rate.
    pre_scale = [p for p in phases if not p.get("scale")] or phases[:1]
    need = sum(p["days"] * p["units_per_day"] for p in pre_scale)
    need += safety_days * pre_scale[-1]["units_per_day"]
    first_qty = max(sup.get("moq", 0), math.ceil(need))
    upfront_ads = sum(p["days"] * p["ad_spend_per_day"] for p in pre_scale[:1])

    def cash_needed(q: int) -> float:
        return samples + landed_cost(m, q)["total"] + upfront_ads

    cap = cash.get("max_cash")
    usable = cap * (1 - cash.get("buffer_pct", 0) / 100) if cap else None
    capped = False
    if usable is not None and cash_needed(first_qty) > usable:
        capped = True
        moq = sup.get("moq", 1)
        first_qty = max(moq, first_qty)
        while first_qty > moq and cash_needed(first_qty) > usable:
            first_qty = max(moq, first_qty - max(1, m["carton"]["units"]))

    first = landed_cost(m, first_qty)
    landed_first = first["per_unit"]["landed"]

    # Phase P&L using first-order landed cost; ads come from the phase's daily budget.
    rows, cum = [], -samples  # tooling is already spread into landed cost
    for p in phases:
        units = p["days"] * p["units_per_day"]
        e = sale_economics(m, p["price"], landed_first, tacos_pct=0)
        ads = p["days"] * p["ad_spend_per_day"]
        profit = units * e["net_profit"] - ads
        cum += profit
        rows.append({
            "phase": p["name"],
            "days": p["days"],
            "units": units,
            "price": r2(p["price"]),
            "revenue": r2(units * p["price"]),
            "ad_spend": r2(ads),
            "tacos_pct": r2(100 * ads / (units * p["price"])) if units else None,
            "profit": r2(profit),
            "cumulative_profit": r2(cum),
            "unlock_next_if": p.get("unlock_next_if", ""),
        })

    reorder_point = math.ceil(steady_per_day * (lead + transit + safety_days))
    cover_days = inv.get("reorder_cover_days", 60)
    reorder_qty = max(sup.get("moq", 0), math.ceil(steady_per_day * cover_days))
    tier_qtys = sorted(t["qty"] for t in sup["tiers"])
    next_tier = next((q for q in tier_qtys if q >= reorder_qty), None)
    if next_tier and next_tier <= reorder_qty * 1.25:
        reorder_qty = next_tier  # round up to a nearby price break

    return {
        "samples_cost": r2(samples),
        "first_order": {
            "qty": first_qty,
            "landed_total": first["total"],
            "landed_per_unit": landed_first,
            "below_moq": first["below_moq"],
            "cartons": first["cartons"],
            "cbm": first["cbm"],
            "cash_needed_incl_samples_and_first_phase_ads": r2(cash_needed(first_qty)),
            "cash_cap_usable": r2(usable) if usable is not None else None,
            "reduced_to_fit_cash": capped,
        },
        "phases": rows,
        "reorder": {
            "reorder_point_units": reorder_point,
            "reorder_qty": reorder_qty,
            "basis": f"{steady_per_day}/day × (lead {lead} + transit {transit} + safety {safety_days} days)",
            "landed_per_unit_at_reorder_qty": landed_cost(m, reorder_qty)["per_unit"]["landed"],
        },
    }


def months_to_break_even(m: dict, pl: dict) -> float | None:
    """P&L basis: months until cumulative profit (after samples and ads) turns positive.
    Resolution is phase ends; beyond the last phase it extrapolates at steady state."""
    rows = pl["phases"]
    d = 0
    for r in rows:
        d += r["days"]
        if r["cumulative_profit"] >= 0:
            return r2(d / 30)
    cum = rows[-1]["cumulative_profit"] if rows else -pl["samples_cost"]
    days = d
    steady = sale_economics(m, m["pricing"]["steady_price"], pl["reorder"]["landed_per_unit_at_reorder_qty"])
    monthly = steady["net_profit"] * m["demand"]["steady_units_per_day"] * 30
    if monthly <= 0:
        return None
    return r2(days / 30 + (-cum) / monthly)


# ------------------------------------------------------------- main run

def run(model: dict, scenario: str) -> dict:
    m = apply_scenario(model, scenario)
    tgt = m.get("targets", {})
    min_margin = tgt.get("min_net_margin_pct", 20)
    pl = plan(m)
    reorder_landed = pl["reorder"]["landed_per_unit_at_reorder_qty"]

    band = m["pricing"].get("band", {})
    candidates = []
    for p in sorted(m["pricing"]["candidates"]):
        e = sale_economics(m, p, reorder_landed)
        e["in_band"] = band.get("low", 0) <= p <= band.get("high", 1e9) if band else None
        e["meets_target"] = e["net_margin_pct"] is not None and e["net_margin_pct"] >= min_margin
        candidates.append(e)
    ok = [c for c in candidates if c["meets_target"] and c["in_band"] is not False]
    # Price near the market's typical price when it clears the margin target; on ties take the higher.
    typical = band.get("typical")
    if ok and typical:
        ok.sort(key=lambda c: (abs(c["price"] - typical), -c["price"]))
    recommended = ok[0]["price"] if ok else None
    m["pricing"]["steady_price"] = recommended or m["pricing"].get("steady_price", candidates[-1]["price"])

    tiers = [landed_cost(m, t["qty"]) for t in sorted(m["supplier"]["tiers"], key=lambda t: t["qty"])]

    warnings = []
    fo, ro = pl["first_order"], pl["reorder"]
    if fo["below_moq"]:
        warnings.append("First order is below the supplier's MOQ or lowest price tier.")
    if fo["reduced_to_fit_cash"]:
        warnings.append("First order was cut to fit the cash cap; it may not cover the launch phases.")
    if fo["cash_cap_usable"] is not None and fo["cash_needed_incl_samples_and_first_phase_ads"] > fo["cash_cap_usable"]:
        warnings.append(
            f"Even at MOQ, cash needed ({fo['cash_needed_incl_samples_and_first_phase_ads']}) exceeds the usable "
            f"cash cap ({fo['cash_cap_usable']}). Negotiate a lower MOQ, buy a smaller test lot "
            "(e.g. from AliExpress), or raise the budget.")
    if ro["reorder_point_units"] >= fo["qty"]:
        warnings.append(
            f"Reorder point ({ro['reorder_point_units']}) is at or above the first order ({fo['qty']}): "
            "place the second purchase order during the launch phase, before the first stock arrives "
            "or soon after, or the product will stock out at steady-state demand.")
    if any(c["price"] < 3 * reorder_landed for c in candidates if c["price"] == recommended):
        warnings.append("Recommended price is under 3x landed cost; little room for error.")

    return {
        "scenario": m["_scenario"],
        "landed_cost_by_tier": [{"qty": t["qty"], **t["per_unit"]} for t in tiers],
        "steady_state_basis_qty": pl["reorder"]["reorder_qty"],
        "break_even_price": price_for_margin(m, reorder_landed, 0),
        "target_margin_price": price_for_margin(m, reorder_landed, min_margin),
        "price_candidates": candidates,
        "recommended_steady_price": recommended,
        "price_warning": None if recommended else
            f"No candidate price in band reaches {min_margin}% net margin. Consider a no-go, a redesign, a cheaper supplier, or a different channel.",
        "plan": pl,
        "months_to_break_even_pnl": months_to_break_even(m, pl),
        "warnings": warnings,
    }


def quick(a: argparse.Namespace) -> dict:
    landed = a.unit_cost * (1 + a.duty_pct / 100) + a.freight_per_unit
    fees = a.price * a.fee_pct / 100 + a.fulfilment
    ads = a.price * a.tacos_pct / 100
    net = a.price - landed - fees - ads
    return {
        "landed_per_unit": r2(landed),
        "channel_fees": r2(fees),
        "ads": r2(ads),
        "net_profit": r2(net),
        "net_margin_pct": r2(100 * net / a.price),
        "price_to_landed_ratio": r2(a.price / landed),
        "note": "Rough check only; excludes returns, storage and import fees beyond duty.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", nargs="?")
    ap.add_argument("--scenario", default="all", choices=["base", "pessimistic", "optimistic", "all"])
    ap.add_argument("--out")
    ap.add_argument("--quick", action="store_true")
    for k in ("price", "unit-cost", "freight-per-unit", "fee-pct", "fulfilment"):
        ap.add_argument(f"--{k}", type=float)
    ap.add_argument("--duty-pct", type=float, default=0)
    ap.add_argument("--tacos-pct", type=float, default=15)
    a = ap.parse_args()

    if a.quick:
        missing = [k for k in ("price", "unit_cost", "freight_per_unit", "fee_pct", "fulfilment")
                   if getattr(a, k) is None]
        if missing:
            ap.error("--quick needs " + ", ".join("--" + k.replace("_", "-") for k in missing))
        out = quick(a)
    else:
        if not a.model:
            ap.error("give a model.json path, or use --quick")
        with open(a.model) as f:
            model = json.load(f)
        names = ["base", "pessimistic", "optimistic"] if a.scenario == "all" else [a.scenario]
        out = {n: run(model, n) for n in names}

    text = json.dumps(out, indent=2)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
