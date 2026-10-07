"""Rank each candidate alone in three synthetic ~50-team fields."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep, field3, lab3

S = os.path.join(sim.ROOT, "strategies")


def cands():
    v2 = sim.load_module(os.path.join(S, "BreadthGuard_v2.py"), "e_v2")
    c1 = sim.load_module(os.path.join(S, "Combined_V1.py"), "e_c1")
    pt = sim.load_module(os.path.join(S, "pairtrading_v5_1_500.py"), "e_pt")
    jm = sim.load_module(os.path.join(S, "jimin_test_v5.py"), "e_jm")
    out = {"Combined_V1": (c1.strategy, None), "BreadthGuard v2": (v2.strategy, None),
           "PairTrading V5.1": (pt.strategy, pt.reset), "jimin_test_v5": (jm.strategy, lambda: jm._START.clear())}
    for E in [1e-6, 1e-4, 1e-3, 1e-2, 0.05]:
        out[f"Combined E={E:g}"] = (c1.__dict__["_rule"].__get__ if False else (lambda E=E: (lambda o: c1._rule(o, E=E)))(), None)
    return out


def run(lab):
    fn, rs = cands()[lab]
    return lab, [sim.metrics(sim.run_window(fn, d, 10.0, rs)) for d in sweep.W]


if __name__ == "__main__":
    with Pool(4) as p:
        C = dict(p.map(run, list(cands())))
    rows = []
    for seed in (1, 2, 3):
        F = field3.field(seed)
        for lab, per in C.items():
            P = {**F, lab: per}
            for nm, idx in (("all", None), ("22-23", sweep.TRAIN), ("24-25", sweep.TEST)):
                s, pos, top3 = field3.place(P, lab, idx)
                rows.append((seed, lab, nm, s, pos, top3))
    df = pd.DataFrame(rows, columns=["field", "candidate", "windows", "score", "position", "top3"])
    t = df.groupby(["candidate", "windows"])[["score", "position", "top3"]].mean().unstack("windows")
    n = len(field3.field(1)) + 1
    print(f"field size {n} (incl. candidate); averaged over 3 random fields")
    print(t.round(2).sort_values(("position", "all")).to_string())
    print(df[df.windows == "all"].pivot(index="candidate", columns="field", values="position").round(1).to_string())
