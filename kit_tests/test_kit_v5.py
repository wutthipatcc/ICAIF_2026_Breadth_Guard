# Run from a copy of the official starter-kit root that also contains Combined_V5.py and run_combined_v5.py.
"""Offline test of the official-kit path: replay one 15-day window, every round, with a live-style portfolio
(weights, positions, value) that is marked and filled like the backtest; validate every upload with the kit."""
import sys, os, json, decimal
import numpy as np
os.environ["COMBINED_V5_STATE"] = "state_test_v5.json"
if os.path.exists("state_test_v5.json"): os.remove("state_test_v5.json")
import Combined_V5 as agent                               # imported before backtest/ is on the path -> kit mode
assert agent.get_daily_close.__module__ == "Combined_V5"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backtest"))
sys.path.insert(0, "/home/user/ICAIF_2026_Breadth_Guard/backtest")
import sim, sweep
from kit.contracts import dumps_json, validate_payload

days = sweep.W[-2]                                        # a 2025 window (hourly marks -> rounds 2-7 too)
cash, shares, uploads, holds = 1_000_000.0, np.zeros(30), [], 0
for day in days:
    pos = sim.CLOSE.index.get_loc(day)
    daily = sim.CLOSE.iloc[pos - 420:pos]
    prices = [sim.OPEN.loc[day].values] + [np.asarray(r) for r in sim.marks(day)[:-1]][:6]
    for n, px in enumerate(prices, start=1):
        value = cash + shares @ px
        port = {"value": value, "cash": cash, "positions": {s: float(q) for s, q in zip(sim.SYMBOLS, shares) if q > 0},
                "weights": {s: float(q * p / value) for s, q, p in zip(sim.SYMBOLS, shares, px)}}
        row = {"id": f"official-{day.date()}-r{n}", "phase": "official", "day": str(day.date()), "number": n}
        obs = {"phase": "official", "round": row, "symbols": sim.SYMBOLS, "as_of": f"{day.date()}T09:00:00-04:00",
               "portfolio": port, "round_state": {}, "daily_close": daily}
        w = agent.kit_decide(obs)
        if w is None:
            holds += 1
            continue
        payload = {"submission_type": "decision", "team_id": "t", "team_token": "x", "phase": "official",
                   "round_id": "official-2026-10-12-r1", "weights": w}
        validate_payload(json.loads(dumps_json(payload).encode(), parse_float=decimal.Decimal), "decision.json")
        t = np.array([w[s] for s in sim.SYMBOLS])
        new = t * value / px
        cash += (shares - new) @ px - np.abs(new - shares) @ px * 1e-3
        shares = new
        uploads.append((row["id"], round(sum(w.values()), 4)))
nav = cash + shares @ sim.CLOSE.loc[days[-1]].values
print("uploads:", uploads)
print("hold rounds (no upload):", holds, "| final NAV", round(nav, 2))
held_live = agent.kit_strategy({**obs, "round": {**row, "number": 3, "id": row["id"][:-1] + "3"}})
print("kit_strategy on a hold round re-submits live weights:", abs(sum(held_live.values()) - sum(port["weights"].values())) < 1e-9)
print("refresh_misses (live Yahoo):", agent.refresh_misses("2026-10-07"))
