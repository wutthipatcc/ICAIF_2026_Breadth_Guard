"""Combined_V5 vs its universe-restricted variants (no TSLA; no TSLA + no Healthcare) in the field5 field."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, field2, field5, lab5, decomp5

FILES = {"Combined_V5": "Combined_V5.py", "V5 no TSLA": "Combined_V5_noTSLA.py",
         "V5 no TSLA, no Healthcare": "Combined_V5_noTSLA_noHealth.py"}


def job(lab):
    def mk():
        m = sim.load_module(os.path.join(field5.ST, FILES[lab]), "ex_" + str(abs(hash(lab))) + str(os.getpid()))
        return m.make_rule()
    a = field5.run(mk(), None, field5.WINS)
    o = field5.run(mk(), None, field5.OCT_WINS)
    days = sim.CLOSE.loc["2022-02-01":"2025-12-31"].index
    v = field5.run_window_rounds(mk(), days)
    return lab, a, o, sim.metrics(v)


if __name__ == "__main__":
    F = field5.field()
    with Pool(3) as p:
        res = {lab: (a, o, fm) for lab, a, o, fm in p.map(job, list(FILES))}
    rows = []
    for lab, (a, o, fm) in res.items():
        r = [lab]
        for per, FF in ((a, F["all"]), (o, F["oct"])):
            P = {**FF, lab: per}
            tr = [l for l in P if l not in lab5.NEAR_CASH]
            t, tt = field2.table(P, list(P), field5.MET), field2.table(P, tr, field5.MET)
            r += [tt.loc[lab, "avg_score"], f"#{list(tt.index).index(lab)+1}/{len(tt)}", t.loc[lab, "avg_score"],
                  f"#{list(t.index).index(lab)+1}/{len(t)}"]
        r += [100 * np.mean([m["return"] for m in a]), 100 * np.mean([m["maxdd"] for m in a]),
              np.mean([m["stability"] for m in a]), 100 * fm["return"], 100 * fm["maxdd"]]
        rows.append(r)
    df = pd.DataFrame(rows, columns=["agent", "65w traders", "place", "65w all", "place ", "Oct traders", "place  ",
                                     "Oct all", "place   ", "avg ret%/win", "avg maxdd%", "avg stab", "2022-25 ret%",
                                     "2022-25 maxdd%"]).set_index("agent")
    # head-to-head: all three in one field
    P = {**F["all"], **{l: res[l][0] for l in res}}
    tr = [l for l in P if l not in lab5.NEAR_CASH]
    h2h = decomp5.dec(P, tr).drop(columns=["sleeve~"]).loc[list(FILES)]
    out = ("# Combined_V5 universe variants\n\nEach variant scored alone against the field5 field (traders = teams "
           "holding a real portfolio).\n\n" + df.round(3).to_markdown() +
           "\n\nAll three together among the traders (65 windows, per-metric average ranks):\n\n" + h2h.round(2).to_markdown() + "\n")
    open(os.path.join(sim.HERE, "results_v5_variants.md"), "w").write(out)
    print(out)
