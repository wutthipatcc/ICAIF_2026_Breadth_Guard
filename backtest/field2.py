"""Evaluator calibrated to the 2026-10-07 web run.

* fees 10 bp of traded notional (web 'Fees paid' implies 9.4-10.7 bp for v1/v2/jimin), with a per-order floor
  (MIN_FEE) because PairTrading's web fees ($193) are ~4x what 10 bp alone gives on its many tiny orders;
* scored metrics: return, stability, max drop and trading (turnover per round), equal weights - reproduces the web
  team table (PT 1.92 / v2 2.28 / jimin 2.83 / v1 2.97 vs web 1.91 / 2.24 / 2.89 / 2.97); volatility instead of
  trading is reported as a check;
* benchmarks: recent winners and yesterday's losers trade every hour on the web (trading 0.72 / 0.19 per round) and
  lose -6.39% / -1.10% per window; here they trade daily, so their cost is raised to land on those averages.
"""
import warnings; warnings.filterwarnings("ignore")
import os, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep

S = os.path.join(sim.ROOT, "strategies")
SCEN = {  # name: (cost_bps, min_fee, whole_shares)
    "A: 10bp + 1c floor": (10.0, 0.01, False),
    "B: 10bp, no floor": (10.0, 0.0, False),
    "C: 10bp + 1c, whole shares": (10.0, 0.01, True),
}
BENCH_COST = {"Kit example (recent winners)": 115.0, "Buy yesterday's losers": 6.0}
HIGHER = {"return": True, "stability": True, "maxdd": False, "vol": False, "trading": False, "worst": False}
METRICS = {"ret+stab+maxdd+trading": ("return", "stability", "maxdd", "trading"),
           "ret+stab+maxdd+vol": ("return", "stability", "maxdd", "vol")}


def fixed():
    v1 = sim.load_module(os.path.join(S, "BreadthGuard_v1.py"), "f_v1")
    v2 = sim.load_module(os.path.join(S, "BreadthGuard_v2.py"), "f_v2")
    pt = sim.load_module(os.path.join(S, "pairtrading_v5_1_500.py"), "f_pt")
    jm = sim.load_module(os.path.join(S, "jimin_test_v5.py"), "f_jm")
    e = {"PairTrading V5.1": (pt.strategy, pt.reset), "BreadthGuard v2": (v2.strategy, None),
         "jimin_test_v5": (jm.strategy, lambda: jm._START.clear()), "BreadthGuard v1": (v1.strategy, None)}
    for f in sim.BENCHMARKS:
        e[f.name] = (f, None)
    return e


def run_entrant(fn, rs, scen, lab=""):
    cost, mf, whole = SCEN[scen]
    cost = BENCH_COST.get(lab, cost)
    return [sim.metrics(sim.run_window(fn, d, cost, rs, min_fee=mf, whole_shares=whole)) for d in sweep.W]


def _job(a):
    lab, scen = a
    fn, rs = fixed()[lab]
    return lab, scen, run_entrant(fn, rs, scen, lab)


def field():
    p = os.path.join(sim.HERE, "_field2_cache.pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    out = {s: {} for s in SCEN}
    with Pool(4) as pool:
        for lab, scen, per in pool.imap_unordered(_job, [(l, s) for l in fixed() for s in SCEN]):
            out[scen][lab] = per
    pickle.dump(out, open(p, "wb"))
    return out


def table(per, labs, mets, idx=None):
    nw = len(per[labs[0]])
    idx = range(nw) if idx is None else idx
    sc = []
    for i in idx:
        R = np.vstack([sim._rank([per[l][i][m] for l in labs], HIGHER[m]) for m in mets])
        sc.append(R.mean(0))
    sc = np.array(sc)
    place = np.vstack([pd.Series(r).rank(method="min").values for r in sc])
    df = pd.DataFrame({"avg_score": sc.mean(0), "avg_place": place.mean(0), "firsts": (place == 1).sum(0),
                       "avg_ret%": [100 * np.mean([per[l][i]["return"] for i in idx]) for l in labs],
                       "maxdd%": [100 * np.mean([per[l][i]["maxdd"] for i in idx]) for l in labs],
                       "trading": [np.mean([per[l][i]["trading"] for i in idx]) for l in labs]}, index=labs)
    return df.sort_values("avg_score")


if __name__ == "__main__":
    F = field()
    sc = "A: 10bp + 1c floor"
    per = F[sc]
    team = ["PairTrading V5.1", "BreadthGuard v2", "jimin_test_v5", "BreadthGuard v1"]
    for mn, mets in METRICS.items():
        print(f"\n== {sc} | {mn}")
        print(table(per, team, mets).round(3).to_string())
        print(table(per, list(per), mets).round(3).to_string())
