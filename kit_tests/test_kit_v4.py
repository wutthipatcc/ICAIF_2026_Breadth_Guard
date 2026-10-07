# Run from a copy of the official starter-kit root that also contains Combined_V4.py and run_combined_v1.py.
"""Offline test of the official-kit path: replay one 15-day window round by round with a fake client."""
import sys, os, json, importlib
import numpy as np, pandas as pd
os.environ["COMBINED_V4_STATE"] = "state_test.json"
if os.path.exists("state_test.json"): os.remove("state_test.json")
import Combined_V4 as agent                               # imported before backtest/ is on the path -> kit mode
assert not hasattr(agent, "testbed") and agent.get_daily_close.__module__ == "Combined_V4"
sys.path.insert(0, "/home/user/ICAIF_2026_Breadth_Guard/backtest")
import sim, sweep
from kit.contracts import dumps_json, validate_payload

days = sweep.W[20]                                         # a window with history
trades, holds = [], 0
for day in days:
    pos = sim.CLOSE.index.get_loc(day)
    daily = sim.CLOSE.iloc[pos - 420:pos]
    for n in range(1, 8):
        row = {"id": f"official-{day.date()}-r{n}", "phase": "official", "day": str(day.date()), "number": n}
        obs = {"phase": "official", "round": row, "symbols": sim.SYMBOLS, "as_of": f"{day.date()}T09:00:00-04:00",
               "portfolio": {}, "round_state": {}, "daily_close": daily}
        w = agent.kit_decide(obs)
        if w is None:
            holds += 1
            continue
        payload = {"submission_type": "decision", "team_id": "t", "team_token": "x", "phase": "official",
                   "round_id": "official-2026-10-12-r1", "weights": w}  # a real id so the schedule check passes
        raw = dumps_json(payload).encode()
        validate_payload(json.loads(raw, parse_float=__import__("decimal").Decimal), "decision.json")
        agent.save_state("official", w, row["id"])
        trades.append((row["id"], sum(w.values())))
print("uploads:", trades)
print("hold rounds (no upload):", holds, "of", 7 * len(days))
print("sample weights:", raw[:160])
