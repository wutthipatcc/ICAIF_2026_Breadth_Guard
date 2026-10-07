"""Final test of strategies/Combined_V5.py in the realistic field (field5). Writes results_combined_v5.md."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import sim, field2, field5, lab5, decomp5

LAB = "Combined_V5"


def sleeve_stats():
    m = sim.load_module(os.path.join(field5.ST, "Combined_V5.py"), "f5_sl")
    rule = m.make_rule()
    seen = []

    def f(obs):
        w = rule(obs)
        if w is not None:
            seen.append(sum(w.values()))
        return w
    for d in field5.WINS:
        field5.run_window_rounds(f, d)
    return np.array(seen)


if __name__ == "__main__":
    F = field5.field()
    _, a, o = lab5.job((LAB, {}))
    L = []
    w = L.append
    md = lambda df: df.round(3).to_markdown()
    w("# Combined_V5 - test results\n")
    w("Evaluator `field5.py`: 10 bp fees, fractional shares, Rounds 2-7 simulated where hourly bars exist (2023-10 on). "
      "Score = mean of the ranks of return, Sharpe (stability), max drawdown and turnover (lower is better). The field "
      "mimics past competitions: cash / near-cash teams, 30-100% equal-weight books, momentum, mean reversion, volatility "
      "targeting, an every-round rebalancer, the kit benchmarks and our own agents.\n")
    for nm, per, FF in (("65 rolling 15-day windows, 2022-02 .. 2025-12", a, F["all"]),
                        ("Earnings-season windows (from Oct 12, 2022-2025 - the Official phase slot)", o, F["oct"])):
        P = {**FF, LAB: per}
        traders = [l for l in P if l not in lab5.NEAR_CASH]
        w(f"\n## {nm}\n\n### Teams that hold a real portfolio\n")
        w(md(field2.table(P, traders, field5.MET)))
        w("\n\n### Whole field (incl. cash and near-cash teams)\n")
        w(md(field2.table(P, list(P), field5.MET)))
        w("\n\nPer-metric average ranks among real-portfolio teams:\n")
        w(md(decomp5.dec(P, traders).drop(columns=["sleeve~"]).head(6)))
    sl = sleeve_stats()
    w(f"\n\n## Size\n\nStock sleeve after each V5 trade: median {np.median(sl):.1%}, 10th-90th pct "
      f"{np.percentile(sl, 10):.1%} - {np.percentile(sl, 90):.1%}, max {sl.max():.1%}.\n")
    m = sim.load_module(os.path.join(field5.ST, "Combined_V5.py"), "f5_full")
    days = sim.CLOSE.loc["2022-02-01":"2025-12-31"].index
    v = field5.run_window_rounds(m.make_rule(), days)
    fm = sim.metrics(v)
    w(f"\n## Whole period in one run (2022-02-01 .. 2025-12-31)\n\nreturn {fm['return']:.2%}, max drawdown "
      f"{fm['maxdd']:.2%}, traded notional {sim.LAST_TURNOVER[0]:.2f}x NAV over {len(days)} days.\n")
    out = "\n".join(L) + "\n"
    open(os.path.join(sim.HERE, "results_combined_v5.md"), "w").write(out)
    print(out)
