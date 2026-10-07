"""Final A/B: BreadthGuard v1 vs v2 (and the micro variant) in the replica evaluator. Writes results.md."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, entrants, sweep

S = os.path.join(sim.ROOT, "strategies")
V1F = sim.load_module(os.path.join(S, "BreadthGuard_v1.py"), "bg_v1_file")
V2 = sim.load_module(os.path.join(S, "BreadthGuard_v2.py"), "bg_v2")
PT = sim.load_module(os.path.join(S, "pairtrading_v5_1_500.py"), "pt")
JM = sim.load_module(os.path.join(S, "jimin_test_v5.py"), "jm")

ENT = {
    "PairTrading V5.1": (PT.strategy, PT.reset),
    "jimin_test_v5": (JM.strategy, lambda: JM._START.clear()),
    "BreadthGuard v1": (V1F.strategy, None),
    "BreadthGuard v1 (v2 file, A/B mode)": (V2.breadth_guard_v1, None),
    "BreadthGuard v2": (V2.strategy, None),
    "BreadthGuard v2 micro": (V2.breadth_guard_micro, None),
}
for f in sim.BENCHMARKS:
    ENT[f.name] = (f, None)
BENCH = [f.name for f in sim.BENCHMARKS]


def run(args):
    lab, cost = args
    fn, rs = ENT[lab]
    out = []
    for d in sweep.W:
        v = sim.run_window(fn, d, cost, rs)
        m = sim.metrics(v)
        r = np.diff(v) / v[:-1]
        dn = np.sqrt(np.mean(np.minimum(r, 0) ** 2))
        m["sortino"] = r.mean() / dn if dn > 1e-15 else 0.0
        out.append(m)
    fp = sim.full_period(fn, rs, cost_bps=cost)[0] if cost == 2.0 else None
    return lab, cost, out, fp


def table(per, labs, idx=None, weights=(1, 1, 1, 1), stab="stability"):
    P = {l: [dict(m, stability=m[stab]) for m in per[l]] for l in labs}
    if idx is not None:
        P = {l: [v[i] for i in idx] for l, v in P.items()}
    return sim.rank_summary(P, labs, weights)


if __name__ == "__main__":
    jobs = [(l, c) for l in ENT for c in (0.0, 2.0, 5.0)]
    res, full = {}, {}
    with Pool(4) as p:
        for lab, cost, out, fp in p.imap_unordered(run, jobs):
            res.setdefault(cost, {})[lab] = out
            if fp is not None:
                full[lab] = fp
    per = res[2.0]
    a = per["BreadthGuard v1"]; b = per["BreadthGuard v1 (v2 file, A/B mode)"]
    same = max(abs(x["return"] - y["return"]) for x, y in zip(a, b))
    L = []
    w = L.append
    w(f"# BreadthGuard v1 vs v2 - replica evaluator results\n")
    w(f"65 windows x 15 trading days, 2022-02-01 .. 2025-12-31, fills at the open, 2 bp cost unless noted, "
      f"hourly marks from 2023-11 (open/close before). v1 A/B mode in the v2 file matches v1 (max return diff {same:.1e}).\n")
    fmt = lambda df: df.round(3).to_markdown()
    for name, bg in (("v1", "BreadthGuard v1"), ("v2", "BreadthGuard v2")):
        w(f"\n## Team table with BreadthGuard {name}\n")
        w(fmt(table(per, ["PairTrading V5.1", "jimin_test_v5", bg])))
        w(f"\n\n## Mock competition with benchmarks - BreadthGuard {name}\n")
        w(fmt(table(per, ["PairTrading V5.1", "jimin_test_v5", bg] + BENCH)))
        w("")
    w("\n## Mock competition - micro variant instead of v2\n")
    w(fmt(table(per, ["PairTrading V5.1", "jimin_test_v5", "BreadthGuard v2 micro"] + BENCH)))
    w("\n\n## Robustness: avg score of BreadthGuard vs Cash in the 7-entrant field\n")
    rows = []
    for nm, kw in [("base (2bp, equal metric weights)", {}),
                   ("metric weights 0.6/0.6/1/1", {"weights": (0.6, 0.6, 1, 1)}),
                   ("stability = Sortino", {"stab": "sortino"}),
                   ("2022-02 .. 2023-12 windows", {"idx": sweep.TRAIN}),
                   ("2024-01 .. 2025-12 windows", {"idx": sweep.TEST})]:
        for bg in ("BreadthGuard v1", "BreadthGuard v2", "BreadthGuard v2 micro"):
            t = table(per, ["PairTrading V5.1", "jimin_test_v5", bg] + BENCH, **kw)
            rows.append((nm, bg, t.loc[bg, "avg_score"], t.loc["Cash only", "avg_score"], list(t.index).index(bg) + 1))
    for cost in (0.0, 5.0):
        for bg in ("BreadthGuard v1", "BreadthGuard v2", "BreadthGuard v2 micro"):
            t = table(res[cost], ["PairTrading V5.1", "jimin_test_v5", bg] + BENCH)
            rows.append((f"cost {cost:g} bp", bg, t.loc[bg, "avg_score"], t.loc["Cash only", "avg_score"], list(t.index).index(bg) + 1))
    w(pd.DataFrame(rows, columns=["scenario", "strategy", "score", "cash score", "place of 7"]).round(3).to_markdown(index=False))
    w("\n\n## Whole period in one run (2022-02-01 .. 2025-12-31)\n")
    fp = pd.DataFrame(full).T[["return", "stability", "maxdd", "vol"]]
    fp["return"] *= 100; fp["maxdd"] *= 100
    w(fp.rename(columns={"return": "return %", "maxdd": "max DD %", "vol": "vol per mark"}).round(4).to_markdown())
    open(os.path.join(sim.HERE, "results.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
