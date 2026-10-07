"""Screenshot field (2026-10-07 web run): PairTrading V5.1, BreadthGuard v2, jimin_test_v5, BreadthGuard v1,
Combined_V3, a NemoV5 stand-in (code not in the repo) and the kit benchmarks. Same evaluator as field2 (10 bp fees,
fractional shares, ranks of return / stability / max drop / trading)."""
import warnings; warnings.filterwarnings("ignore")
import os, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep, field2

S = os.path.join(sim.ROOT, "strategies")
SCEN = "B: 10bp, no floor"
TEAM = ["PairTrading V5.1", "BreadthGuard v2", "Combined_V3", "jimin_test_v5", "BreadthGuard v1", "NemoV5 (proxy)"]
BENCH = [f.name for f in sim.BENCHMARKS]
MET = field2.METRICS["ret+stab+maxdd+trading"]


def nemo_proxy(obs):
    """High-exposure 12-1 momentum book (top 12, 95% invested, partial daily rebalance). Calibrated to the web
    NemoV5 row: ~0.66% / window, ~3.3% max drop, ~0.015 trading per round."""
    d = obs["_daily"]
    port = obs["portfolio"]
    if len(d) < 253:
        return None
    m = d.iloc[-22].values / d.iloc[-253].values - 1
    top = np.argsort(-m)[:12]
    t = np.zeros(30); t[top] = 0.95 / 12
    cur = np.array([port["weights"].get(s, 0.0) for s in obs["symbols"]])
    if port["positions"] and np.abs(t - cur).sum() < 0.30:
        return None
    new = t if not port["positions"] else cur + 0.5 * (t - cur)
    return dict(zip(obs["symbols"], new.tolist()))


nemo_proxy.name = "NemoV5 (proxy)"


def _job(lab):
    if lab == "Combined_V3":
        m = sim.load_module(os.path.join(S, "Combined_V3.py"), "f4_v3")
        return lab, field2.run_entrant(m.make_rule(), None, SCEN)
    if lab == "NemoV5 (proxy)":
        return lab, field2.run_entrant(nemo_proxy, None, SCEN)
    return lab, None


def field():
    p = os.path.join(sim.HERE, "_field4_cache.pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    out = dict(field2.field()[SCEN])
    with Pool(2) as pool:
        for lab, per in pool.map(_job, ["Combined_V3", "NemoV5 (proxy)"]):
            out[lab] = per
    pickle.dump(out, open(p, "wb"))
    return out


def full_period(fn, cost=10.0):
    days = sim.CLOSE.loc["2022-02-01":"2025-12-31"].index
    v = sim.run_window(fn, days, cost)
    return sim.metrics(v), v


if __name__ == "__main__":
    F = field()
    print(field2.table(F, TEAM, MET).round(3).to_string())
    print(field2.table(F, TEAM + BENCH, MET).round(3).to_string())
