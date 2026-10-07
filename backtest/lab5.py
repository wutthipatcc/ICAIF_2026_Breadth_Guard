"""Combined_V5 sweeps in the realistic field (field5). Usage: python3 lab5.py configs/v5a.json"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep, field2, field5

NEAR_CASH = {"Cash only", "Near-cash EW 2e-05", "Near-cash EW 2e-04", "PairTrading V5.1", "Combined_V4"}


def v5(**kw):
    m = sim.load_module(os.path.join(field5.ST, "Combined_V5.py"), "l5_" + str(os.getpid()))
    m.load_earnings_csv(os.path.join(sim.ROOT, "data", "earnings_days.csv"))
    return m.make_rule(**kw)


def job(a):
    lab, kw = a
    return lab, field5.run(v5(**kw), None, field5.WINS), field5.run(v5(**kw), None, field5.OCT_WINS)


def line(lab, a, o, F):
    parts = []
    for nm, per, FF in (("all", a, F["all"]), ("oct", o, F["oct"])):
        P = {**FF, lab: per}
        t = field2.table(P, list(P), field5.MET)
        tr = field2.table(P, [l for l in P if l not in NEAR_CASH], field5.MET)
        parts.append(f"{nm}: {t.loc[lab,'avg_score']:.2f} #{list(t.index).index(lab)+1}/{len(t)} "
                     f"traders #{list(tr.index).index(lab)+1} ({tr.loc[lab,'avg_score']:.2f})")
    r = np.mean([m["return"] for m in a]) * 100
    dd = np.mean([m["maxdd"] for m in a]) * 100
    tr_ = np.mean([m["trading"] for m in a])
    return f"{lab:34s} ret {r:.3f}% dd {dd:.2f}% trn {tr_:.4f} | " + " | ".join(parts)


if __name__ == "__main__":
    F = field5.field()
    cfg = json.load(open(sys.argv[1]))
    with Pool(4) as p:
        for lab, a, o in p.imap_unordered(job, list(cfg.items())):
            print(line(lab, a, o, F), flush=True)
