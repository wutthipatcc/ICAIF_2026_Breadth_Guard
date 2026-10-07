"""Per-metric average ranks for a candidate in the screenshot field."""
import warnings; warnings.filterwarnings("ignore")
import sys, json, os, numpy as np, pandas as pd
import sim, field2, field4, lab4


def decomp(P, labs):
    out = {}
    for m in field4.MET:
        R = np.vstack([sim._rank([P[l][i][m] for l in labs], field2.HIGHER[m]) for i in range(len(P[labs[0]]))])
        out[m] = R.mean(0)
    return pd.DataFrame(out, index=labs).assign(score=lambda d: d.mean(1)).sort_values("score")


if __name__ == "__main__":
    F = field4.field()
    cands = {"V1": None}
    cfg = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    v1 = sim.load_module(os.path.join(sim.ROOT, "strategies", "Combined_V1.py"), "d_v1")
    P = dict(F)
    P["Combined_V1"] = field2.run_entrant(v1.strategy, None, field4.SCEN)
    for lab, kw in cfg.items():
        P[lab] = field2.run_entrant(lab4.make(**kw), None, field4.SCEN)
    for nm, base in (("team", field4.TEAM), ("mock", field4.TEAM + field4.BENCH)):
        labs = base + [l for l in P if l not in F]
        print(f"== {nm}\n", decomp(P, labs).round(2).to_string())
