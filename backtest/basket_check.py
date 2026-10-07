"""Fixed-basket hold agents (jimin_bigtech7 and the jimin_finhealth variants) vs the field5 field.

Periods: the 65 rolling windows 2022-02 .. 2025-12, the 4 Oct-12 windows 2022-25, and the 15-day windows of 2026
(Jan 2 .. Oct 6; data/recent_*.csv appended to the daily history, hourly marks where Yahoo has them).
Writes results_finhealth.md."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, field2, field5, lab5

ST = field5.ST
D = os.path.join(sim.ROOT, "data")


def _extend():
    for nm, attr in (("open", "OPEN"), ("close", "CLOSE")):
        r = pd.read_csv(os.path.join(D, f"recent_{nm}.csv"), index_col=0, parse_dates=True)[sim.SYMBOLS]
        old = getattr(sim, attr)
        setattr(sim, attr, pd.concat([old[old.index < r.index[0]], r]))
    sim._MARK_CACHE.clear()


_extend()
DAYS26 = sim.CLOSE.loc["2026-01-02":].index
WIN26 = [DAYS26[i:i + 15] for i in range(0, len(DAYS26) - 14, 15)]


def bigtech7_module():
    p = os.path.join(sim.HERE, "_bigtech7.py")
    open(p, "w").write('''from testbed import zero_weights
BASKET = ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA"]
def strategy(observation):
    port = observation["portfolio"]
    if bool(port.get("positions")) or sum((port.get("weights") or {}).values()) > 0:
        return None
    if observation["round"]["number"] != 1:
        return None
    out = zero_weights(); out.update({s: 0.25 / 7 for s in BASKET}); return out
''')
    return sim.load_module(p, "bt7")


def ours():
    fh = sim.load_module(os.path.join(ST, "jimin_finhealth.py"), "fh_" + str(os.getpid()))
    e = {"jimin_bigtech7 (25%)": bigtech7_module().strategy, "bigtech6 no TSLA (25%)": fh.bigtech6,
         "Fin+Health 10 (25%)": fh.finhealth25, "Fin+Health 10 (15%)": fh.finhealth15,
         "Fin+Health 10 (40%)": fh.finhealth40, "Tilt 2/3 FH + 1/3 tech (25%)": fh.finhealth_tilt25,
         "Tilt 2/3 FH + 1/3 tech (15%)": fh.tilt15}
    for lab, f in (("Combined_V5", "Combined_V5.py"), ("V5 no TSLA, no Healthcare", "Combined_V5_noTSLA_noHealth.py")):
        m = sim.load_module(os.path.join(ST, f), "c5_" + lab[:3] + str(os.getpid()))
        e[lab] = m.make_rule()
    return e


CANDS = list(ours().keys())


def job(a):
    lab, period = a
    wins = {"all": field5.WINS, "oct": field5.OCT_WINS, "2026": WIN26}[period]
    if lab in CANDS:
        fn, rs = ours()[lab], None
    else:
        fn, rs = field5.entrants()[lab]
    return lab, period, field5.run(fn, rs, wins, lab)


if __name__ == "__main__":
    F = field5.field()
    gen = [l for l in field5.entrants() if l not in CANDS]
    jobs = [(l, p) for l in CANDS for p in ("all", "oct", "2026")] + [(l, "2026") for l in gen]
    R = {"all": dict(F["all"]), "oct": dict(F["oct"]), "2026": {}}
    with Pool(4) as p:
        for lab, period, per in p.imap_unordered(job, jobs):
            R[period][lab] = per
    L = ["# Fixed-basket agents: big tech vs Finance + Healthcare\n",
         "Each candidate is scored ALONE against the field5 field (cash / near-cash teams, equal-weight, momentum, "
         "mean-reversion, vol-target books, our earlier agents, kit benchmarks). Lower score is better. "
         "'traders' = teams holding a real portfolio.\n"]
    rows = []
    for lab in CANDS:
        r = [lab]
        for period in ("all", "oct", "2026"):
            base = {k: v for k, v in R[period].items() if k not in CANDS}
            P = {**base, lab: R[period][lab]}
            tr = [l for l in P if l not in lab5.NEAR_CASH]
            t, tt = field2.table(P, list(P), field5.MET), field2.table(P, tr, field5.MET)
            r += [f"{tt.loc[lab,'avg_score']:.2f} (#{list(tt.index).index(lab)+1}/{len(tt)})",
                  f"{t.loc[lab,'avg_score']:.2f} (#{list(t.index).index(lab)+1}/{len(t)})",
                  f"{100*np.mean([m['return'] for m in R[period][lab]]):.2f}% / {100*np.mean([m['maxdd'] for m in R[period][lab]]):.2f}%"]
        rows.append(r)
    cols = ["agent"]
    for p in ("2022-25 65w", "Oct 2022-25", f"2026 ({len(WIN26)}w)"):
        cols += [f"{p} traders", f"{p} all", f"{p} ret / maxdd"]
    df = pd.DataFrame(rows, columns=cols).set_index("agent")
    for p in ("2022-25 65w", "Oct 2022-25", f"2026 ({len(WIN26)}w)"):
        L.append(f"\n## {p}\n")
        L.append(df[[c for c in df.columns if c.startswith(p)]].to_markdown())
    # sector returns in 2026
    c = sim.CLOSE.loc["2025-12-31":]
    sec = {"Big tech 7": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA"], "Finance": ["JPM", "BAC", "GS", "V", "PYPL"],
           "Healthcare": ["LLY", "JNJ", "UNH", "PFE", "TMO"], "All 30": sim.SYMBOLS}
    L.append("\n\n## 2026 year-to-date equal-weight return by group (to 2026-10-06)\n")
    L.append(pd.DataFrame({k: [100 * (c[v].iloc[-1] / c[v].iloc[0] - 1).mean(),
                               100 * (c[v].iloc[-21:].iloc[-1] / c[v].iloc[-21] - 1).mean()] for k, v in sec.items()},
                          index=["YTD %", "last 20 days %"]).T.round(2).to_markdown())
    out = "\n".join(L) + "\n"
    open(os.path.join(sim.HERE, "results_finhealth.md"), "w").write(out)
    print(out)
