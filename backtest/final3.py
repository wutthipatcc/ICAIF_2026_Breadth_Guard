"""Final test of Combined_V1 in the calibrated evaluator (field2). Writes results_combined_v1.md."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep, field2

V3 = os.path.join(sim.ROOT, "strategies", "Combined_V1.py")
LAB = "Combined_V1"
TEAM = ["PairTrading V5.1", "BreadthGuard v2", "jimin_test_v5"]
BENCH = [f.name for f in sim.BENCHMARKS]


def job(scen):
    m = sim.load_module(V3, "v3_" + scen[0])
    return scen, field2.run_entrant(m.strategy, None, scen)


if __name__ == "__main__":
    F = field2.field()
    with Pool(3) as p:
        res = dict(p.map(job, list(field2.SCEN)))
    mT = field2.METRICS["ret+stab+maxdd+trading"]
    mV = field2.METRICS["ret+stab+maxdd+vol"]
    B = "B: 10bp, no floor"
    PB = {**F[B], LAB: res[B]}
    L = []
    w = L.append
    md = lambda df: df.round(3).to_markdown()
    w("# Combined_V1 - test results\n")
    w("Evaluator `field2.py`: 65 windows x 15 days (2022-02-01 .. 2025-12-31), 10 bp fees, fractional shares, ranks of "
      "return / stability / max drop / trading, equal weights (calibrated to the 2026-10-07 web run).\n")
    w("\n## 1. My strategies ranked against each other (team table)\n")
    w(md(field2.table(PB, TEAM + [LAB], mT)))
    w("\n\n## 2. Mock competition with benchmarks (v1 dropped, Combined_V1 added - 8 entrants)\n")
    w(md(field2.table(PB, TEAM + [LAB] + BENCH, mT)))
    w("\n\n## 3. Mock competition with everything (9 entrants)\n")
    w(md(field2.table(PB, list(PB), mT)))
    rows = []

    def add(name, P, labs, mets, idx=None):
        t = field2.table(P, labs, mets, idx)
        rows.append((name, t.loc[LAB, "avg_score"], t.loc["PairTrading V5.1", "avg_score"], t.loc["Cash only", "avg_score"],
                     list(t.index).index(LAB) + 1, len(labs)))

    labs8 = TEAM + [LAB] + BENCH
    add("main (B, trading metric)", PB, labs8, mT)
    add("2022-02 .. 2023-12 windows", PB, labs8, mT, sweep.TRAIN)
    add("2024-01 .. 2025-12 windows", PB, labs8, mT, sweep.TEST)
    add("volatility instead of trading", PB, labs8, mV)
    add("5 metrics (+vol)", PB, labs8, ("return", "stability", "maxdd", "trading", "vol"))
    for dec in (6, 4):
        rd = lambda x: {k: (round(v, dec) if k in ("return", "maxdd", "trading", "vol") else v) for k, v in x.items()}
        add(f"metrics rounded to {dec} decimals", {k: [rd(x) for x in v] for k, v in PB.items()}, labs8, mT)
    for sc in ("A: 10bp + 1c floor", "C: 10bp + 1c, whole shares"):
        add(f"stress {sc}", {**F[sc], LAB: res[sc]}, labs8, mT)
    w("\n\n## 4. Robustness (8-entrant field: team + Combined_V1 + benchmarks)\n")
    w(pd.DataFrame(rows, columns=["scenario", "Combined_V1 score", "PairTrading", "Cash", "Combined_V1 place", "of"]).round(3).to_markdown(index=False))
    m = sim.load_module(V3, "v3_full")
    days = sim.CLOSE.loc["2022-02-01":"2025-12-31"].index
    v = sim.run_window(m.strategy, days, 10.0)
    fm = sim.metrics(v)
    w(f"\n\n## 5. Whole period in one run\n\nreturn {100*fm['return']:.4f}%  max drop {100*fm['maxdd']:.4f}%  "
      f"stability {fm['stability']:.4f}  - it makes essentially nothing; it is built to rank, not to earn.\n")
    open(os.path.join(sim.HERE, "results_combined_v1.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
