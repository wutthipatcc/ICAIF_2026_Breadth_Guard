"""Per-metric average ranks of V5 candidates vs the realistic field (traders only and full field)."""
import warnings; warnings.filterwarnings("ignore")
import sys, json, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, field2, field5, lab5


def dec(P, labs):
    out = {m: np.vstack([sim._rank([P[l][i][m] for l in labs], field2.HIGHER[m]) for i in range(len(P[labs[0]]))]).mean(0)
           for m in field5.MET}
    d = pd.DataFrame(out, index=labs)
    d["score"] = d.mean(1)
    d["ret%"] = [100 * np.mean([x["return"] for x in P[l]]) for l in labs]
    d["sleeve~"] = np.nan
    return d.sort_values("score")


if __name__ == "__main__":
    F = field5.field()
    cfg = json.load(open(sys.argv[1]))
    with Pool(4) as p:
        res = {lab: a for lab, a, o in p.map(lab5.job, list(cfg.items()))}
    P = {**F["all"], **res}
    keep = ["BreadthGuard v2", "Combined_V3", "jimin_test_v5", "EW 30% buy & hold"] + list(res)
    tr = [l for l in F["all"] if l not in lab5.NEAR_CASH] + list(res)
    print("traders + candidates (each candidate competes against the others too):")
    print(dec(P, tr).loc[keep].round(2).to_string())
