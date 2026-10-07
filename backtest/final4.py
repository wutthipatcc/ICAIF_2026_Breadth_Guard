"""Final test of strategies/Combined_V4.py against the screenshot field (field4). Writes results_combined_v4.md.

Tables mirror the web tool: (1) team strategies ranked against each other, (2) the whole period in one run,
(3) mock competition including benchmarks; then robustness checks."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep, field2, field4

ST = os.path.join(sim.ROOT, "strategies")
LAB = "Combined_V4"
TEAM = field4.TEAM + [LAB]
BENCH = field4.BENCH
MET = field4.MET


def entrant(lab):
    if lab == LAB:
        m = sim.load_module(os.path.join(ST, "Combined_V4.py"), "f4_v4_" + str(os.getpid()))
        return m.strategy, None
    if lab == "Combined_V1":
        m = sim.load_module(os.path.join(ST, "Combined_V1.py"), "f4_v1_" + str(os.getpid()))
        return m.strategy, None
    if lab == "Combined_V3":
        m = sim.load_module(os.path.join(ST, "Combined_V3.py"), "f4_v3_" + str(os.getpid()))
        return m.make_rule(), None
    if lab == "NemoV5 (proxy)":
        return field4.nemo_proxy, None
    return field2.fixed()[lab]


def job_windows(a):
    lab, scen = a
    fn, rs = entrant(lab)
    return lab, scen, field2.run_entrant(fn, rs, scen, lab)


def job_full(lab):
    fn, rs = entrant(lab)
    if rs:
        rs()
    days = sim.CLOSE.loc["2022-02-01":"2025-12-31"].index
    v = sim.run_window(fn, days, 10.0, rs)
    m = sim.metrics(v)
    m["trading"] = sim.LAST_TURNOVER[0] / (len(days))  # per Round-1 decision day
    return lab, m


def decomp(P, labs):
    out = {}
    for m in MET:
        R = np.vstack([sim._rank([P[l][i][m] for l in labs], field2.HIGHER[m]) for i in range(len(P[labs[0]]))])
        out[f"rank {m}"] = R.mean(0)
    return pd.DataFrame(out, index=labs)


if __name__ == "__main__":
    F = field4.field()
    stress = ["A: 10bp + 1c floor", "C: 10bp + 1c, whole shares"]
    with Pool(4) as p:
        res = {}
        for lab, scen, per in p.imap_unordered(job_windows, [(LAB, field4.SCEN), ("Combined_V1", field4.SCEN)]
                                               + [(LAB, s) for s in stress]):
            res[(lab, scen)] = per
        full = dict(p.map(job_full, TEAM))
    P = {**F, LAB: res[(LAB, field4.SCEN)]}
    L = []
    w = L.append
    md = lambda df: df.round(3).to_markdown()
    w("# Combined_V4 - test results\n")
    w("Evaluator `field4.py` (= `field2.py` calibration): 65 windows x 15 trading days, 2022-02-01 .. 2025-12-31, "
      "10 bp fees, fractional shares, equal-weight ranks of return / stability / max drop / trading. The field is the "
      "2026-10-07 web screenshot field; NemoV5 is a stand-in (its code is not in the repo) calibrated to its web row.\n")
    t1 = field2.table(P, TEAM, MET)
    w("\n## 1. My strategies ranked against each other (65 three-week tests)\n")
    w(md(t1.join(decomp(P, TEAM))))
    w("\n\n## 2. The whole period in one run (2022-02-01 .. 2025-12-31)\n")
    fd = pd.DataFrame(full).T[["return", "stability", "maxdd", "trading"]]
    ranks = pd.DataFrame({m: sim._rank(fd[m].values, field2.HIGHER[m]) for m in MET}, index=fd.index)
    fd.insert(0, "score", ranks.mean(1))
    fd["return"] *= 100; fd["maxdd"] *= 100
    w(fd.sort_values("score").rename(columns={"return": "return%", "maxdd": "maxdd%"}).to_markdown(floatfmt=".6g"))
    t3 = field2.table(P, TEAM + BENCH, MET)
    w("\n\n## 3. Mock competition including benchmarks\n")
    w(md(t3))
    rows = []

    def add(name, PP, labs, mets=MET, idx=None):
        t = field2.table(PP, labs, mets, idx)
        rows.append((name, t.loc[LAB, "avg_score"], t.loc["PairTrading V5.1", "avg_score"],
                     t.loc["Cash only", "avg_score"] if "Cash only" in t.index else np.nan,
                     list(t.index).index(LAB) + 1, len(labs)))

    labs = TEAM + BENCH
    add("mock competition (main)", P, labs)
    add("2022-02 .. 2023-12 windows", P, labs, idx=sweep.TRAIN)
    add("2024-01 .. 2025-12 windows", P, labs, idx=sweep.TEST)
    add("volatility instead of trading", P, labs, field2.METRICS["ret+stab+maxdd+vol"])
    add("5 metrics (+volatility)", P, labs, ("return", "stability", "maxdd", "trading", "vol"))
    for dec in (6, 4):
        rd = lambda x: {k: (round(v, dec) if k in ("return", "maxdd", "trading", "vol") else v) for k, v in x.items()}
        add(f"metrics rounded to {dec} decimals", {k: [rd(x) for x in v] for k, v in P.items()}, labs)
    PV1 = {**P, "Combined_V1": res[("Combined_V1", field4.SCEN)]}
    add("+ Combined_V1 in the field", PV1, labs + ["Combined_V1"])
    F2 = field2.field()
    for sc in stress:
        PS = {**F2[sc], LAB: res[(LAB, sc)]}
        for k in ("Combined_V3", "NemoV5 (proxy)"):
            PS[k] = F[k]                                   # not re-run under stress (unchanged order of magnitude)
        add(f"stress {sc}", PS, labs)
    w("\n\n## 4. Robustness (mock-competition field unless noted)\n")
    w(pd.DataFrame(rows, columns=["scenario", "Combined_V4", "PairTrading", "Cash", "V4 place", "of"]).round(3)
      .to_markdown(index=False))
    out = "\n".join(L) + "\n"
    open(os.path.join(sim.HERE, "results_combined_v4.md"), "w").write(out)
    print(out)
