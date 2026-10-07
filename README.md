# BreadthGuard v2

`strategies/BreadthGuard_v2.py` is the updated strategy (entry point `strategy`). `strategies/BreadthGuard_v1.py`
is the previous version; the two teammates' strategies are in `strategies/` for the comparisons.

## What changed

| | v1 | v2 |
|---|---|---|
| Base stock exposure | 25% | **15%** |
| Exposure after a breadth-confirmed shock | 40% | **36%** (2.4 × base) |
| Momentum tilt | absolute 0.25%/z (= 0.3 × slot at 25%) | **relative 0.6 × S/30 per z** |
| No-trade band | 5% absolute | **5% × S/25%** (scales with the sleeve) |
| Signal, earnings-miss rule, shock trigger, Round-1 only, 30% cap, k = 0.5 | unchanged | unchanged |

`breadth_guard_v1()` in the v2 file reproduces v1 exactly (checked: identical results in all 65 windows).

## Results (local replica of the comparison tool)

The replica (`backtest/sim.py`) reproduces the web tool's numbers closely. Average scores for your 3 strategies:
PairTrading 1.61 (web 1.59), jimin 2.11 (2.17), BreadthGuard v1 2.28 (2.24). It also puts the top 5 of the
benchmark table in the same order. Full tables are in `backtest/results.md`.

Mock competition with the benchmarks (7 entrants, 65 windows; lower score is better):

| | v1 score / place | v2 score / place | Cash |
|---|---|---|---|
| all 65 windows | 3.58 / 4th | **3.29 / 3rd** | 3.07 |
| 2022-02 .. 2023-12 | 3.57 / 4th | 3.29 / 3rd | 2.74 |
| 2024-01 .. 2025-12 | 3.59 / 4th | **3.28 / 2nd (beats Cash)** | 3.41 |

Among your 3 strategies only, v2 moves from 3rd (2.28) to 2nd (1.98), ahead of jimin_test_v5. v2 scores better than v1
under 0, 2 and 5 bp costs, with 0.6/0.6/1/1 metric weights, and with Sortino as the stability metric. Over the whole
period in one run, v2 returns 28.0% with an 8.0% max drawdown, against 24.1% and 9.0% for v1.

## Can it beat Cash?

Only by becoming cash. The score averages four ranks, and two of them are max drawdown and volatility. Cash ranks
1st on both in every window. PairTrading holds about 0.003%–3% in stocks and ranks 2nd on both in every window. Any
strategy with real exposure therefore ranks 3rd at best on half the score. To catch up, it would have to rank about
1.1 places better on return plus stability in every window. No signal, weighting or timing rule I tested got near
that across 2022–23 (sweeps are in `backtest/`).

`breadth_guard_micro()` is the same rule at 0.001% exposure, i.e. $10 of $1M invested. It ranks **1st, ahead of
Cash (2.95 vs 3.07)**, in 5 of 7 robustness scenarios. That is purely a quirk of rank-based scoring. It earns
nothing, and it gets nowhere if the real testbed only fills whole shares. It is in the file if you want it; the
default `strategy` stays on v2.

## Correlation review (`backtest/corr_report.py`)

* The average pairwise correlation of daily returns, 2022–2025, is 0.29.
* The tightest clusters are XOM/CVX (0.85), the banks JPM/BAC/GS (0.76–0.80) and mega-cap tech
  (MSFT/AMZN/NVDA/GOOGL/AAPL/META, 0.61–0.67).
* The least connected names are UNH, JNJ, T, LLY, WMT and KO (0.13–0.21 average correlation to the rest).
* When the 63-day average correlation is in its top quartile, the next 15 days are about 1.7× more volatile
  (std 5.1% vs 2.9%). Returns are not lower.
* **Tested and not adopted:** correlation-aware minimum-variance weights (shrunk covariance, 6–10% caps,
  63/126/252-day windows), inverse-vol and inverse-vol×correlation weights, a correlation gate, a trend (100-day MA)
  gate, and volatility targeting. Each one lowered volatility in absolute terms but left the drawdown and volatility
  ranks unchanged, and lost on the return or stability ranks (scores 3.37–3.61 against 3.29).

## Reproduce

```
pip install yfinance pandas numpy tabulate
python3 data/fetch.py                 # prices (not committed)
cd backtest
python3 check_replica.py              # replica vs the web tool's rankings
python3 corr_report.py                # correlation review
python3 final_eval.py                 # v1 vs v2 vs micro -> results.md
python3 comp.py && python3 comp_eval.py configs/cfg4.json   # parameter sweeps
```

Replica assumptions: one Round-1 decision per day, filled at the open; 2 bp cost; marks every hour where Yahoo has
hourly bars (from Nov 2023), open and close before that; stability = mean / std of mark-to-mark returns. These are
inferred from the screenshots, not taken from the official evaluator.
