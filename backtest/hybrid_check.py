"""jimin_hybrid_better_weight (original) vs jimin_hybrid_fh_nvda (Finance + Healthcare first, NVDA concentrated,
INTC/TSLA banned) and share variants, each scored alone against the field5 field in 2022-25 (65 windows), the Oct
windows 2022-25 and the 2026 windows (Jan .. Oct 6). Writes results_hybrid_fh_nvda.md."""
import warnings; warnings.filterwarnings("ignore")
import os, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
import basket_check as bc                           # extends the price history to 2026-10-06
import sim, field2, field5

ST = field5.ST
CANDS = {
    "original hybrid (INTC/CRM/TSLA -> NVDA)": ("jimin_hybrid_better_weight.py", {}),
    "fh_nvda default (NVDA 20%, Fin+Hlth 55%)": ("jimin_hybrid_fh_nvda.py", {}),
    "fh_nvda NVDA 10%, Fin+Hlth 55%": ("jimin_hybrid_fh_nvda.py", {"NVDA_SHARE": 0.10}),
    "fh_nvda NVDA 30%, Fin+Hlth 55%": ("jimin_hybrid_fh_nvda.py", {"NVDA_SHARE": 0.30}),
    "fh_nvda NVDA 20%, Fin+Hlth 67%": ("jimin_hybrid_fh_nvda.py", {"PRIORITY_SHARE": 0.67}),
    "fh_nvda NVDA 20%, Fin+Hlth 40%": ("jimin_hybrid_fh_nvda.py", {"PRIORITY_SHARE": 0.40}),
}
PERIODS = {"2022-25 (65w)": field5.WINS, "Oct 2022-25 (4w)": field5.OCT_WINS, f"2026 ({len(bc.WIN26)}w)": bc.WIN26}


def mk(lab):
    f, kw = CANDS[lab]
    m = sim.load_module(os.path.join(ST, f), "hy_" + str(abs(hash(lab))) + str(os.getpid()))
    for k, v in kw.items():
        setattr(m, k, v)
    return m.strategy


def job(a):
    lab, period = a
    if lab in CANDS:
        return lab, period, field5.run(mk(lab), None, PERIODS[period], lab)
    fn, rs = field5.entrants()[lab]
    return lab, period, field5.run(fn, rs, PERIODS[period], lab)


def field26():
    p = os.path.join(sim.HERE, "_field26_cache.pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    k = list(PERIODS)[2]
    with Pool(4) as pool:
        out = {lab: per for lab, _, per in pool.map(job, [(l, k) for l in field5.entrants()])}
    pickle.dump(out, open(p, "wb"))
    return out


if __name__ == "__main__":
    F5 = field5.field()
    base = {"2022-25 (65w)": F5["all"], "Oct 2022-25 (4w)": F5["oct"], list(PERIODS)[2]: field26()}
    with Pool(4) as pool:
        res = {(l, p): per for l, p, per in pool.map(job, [(l, p) for l in CANDS for p in PERIODS])}
    L = ["# jimin_hybrid: original vs Finance + Healthcare / NVDA version\n",
         "Each agent scored ALONE against the 20-team field5 field (cash, near-cash, equal-weight, momentum, "
         "mean-reversion, vol-target teams, our agents incl. Combined_V4 / PairTrading, kit benchmarks). Lower is better.\n"]
    for period in PERIODS:
        rows = []
        for lab in CANDS:
            P = {**base[period], lab: res[(lab, period)]}
            t = field2.table(P, list(P), field5.MET)
            near = [l for l in P if l in ("Combined_V4", "PairTrading V5.1", "Cash only", "Near-cash EW 2e-05", lab)]
            tn = field2.table(P, near, field5.MET)
            per = res[(lab, period)]
            rows.append([lab, round(t.loc[lab, "avg_score"], 2), f"#{list(t.index).index(lab)+1}/{len(t)}",
                         f"#{list(tn.index).index(lab)+1}/5", round(np.mean([m["stability"] for m in per]), 4),
                         f"{100*np.mean([m['return'] for m in per]):.5f}%", f"{100*np.mean([m['maxdd'] for m in per]):.5f}%"])
        v4 = field2.table(base[period], list(base[period]), field5.MET).loc["Combined_V4", "avg_score"]
        pt = field2.table(base[period], list(base[period]), field5.MET).loc["PairTrading V5.1", "avg_score"]
        L.append(f"\n## {period}  (without the candidate: Combined_V4 {v4:.2f}, PairTrading {pt:.2f})\n")
        L.append(pd.DataFrame(rows, columns=["agent", "score", "place (20 teams)", "place among near-cash 5",
                                             "avg stability", "avg return", "avg maxdd"]).set_index("agent").to_markdown())
    out = "\n".join(L) + "\n"
    open(os.path.join(sim.HERE, "results_hybrid_fh_nvda.md"), "w").write(out)
    print(out)
