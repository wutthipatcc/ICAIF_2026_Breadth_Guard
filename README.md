# BreadthGuard

* `strategies/Combined_V1.py`: **Combined_V1**, the agent that ranks above Cash and PairTrading (below).
* `strategies/BreadthGuard_v2.py`: re-sized BreadthGuard that actually earns returns (section further down).

## Combined_V1 (best competition rank)

**How the score works** (`backtest/field2.py`). The score is the average rank on four metrics: return, stability,
max drop and trading. With 10 bp fees and fractional shares, this replica reproduces the web team table
(1.93 / 2.27 / 2.82 / 2.99 vs web 1.91 / 2.24 / 2.89 / 2.97) and the top 5 of the mock competition to within
about 0.07.

**What the three agents do:**

| Agent | Trading view | Why it ranks where it does |
|---|---|---|
| PairTrading V5.1 | 0.003%-0.03% in stocks, +1-3% after any -2% day. The pair signals are multiplied by about 1e-6, so they hardly change the weights; it rebalances daily with many tiny orders | 2nd only to Cash on max drop and trading in every window; the return and stability ranks decide the rest |
| BreadthGuard v2 | 15% -> 36% momentum book, breadth-confirmed shock buying | real returns (+23.9% over the period), but 3rd or worse on max drop and trading |
| jimin_test_v5 | 25% -> 40% residual-momentum book, shock cut-off at day 10 | best stock selection of the three, but the most exposure, so the worst risk ranks |

**Design.** Stability ignores position size, and max drop and trading only reward holding less. So Combined_V1:

* holds less than PairTrading: 0.001% of capital, 0.008% after a shock;
* picks the best 15-day risk-adjusted path: inverse-volatility weights (the least-correlated names get the most)
  tilted by jimin's residual momentum;
* keeps BreadthGuard's breadth-confirmed shock step-up and the earnings-miss exclusion;
* buys once and holds, so it trades almost nothing.

**Results** (`backtest/results_combined_v1.md`; team + Combined_V1 + benchmarks, 65 windows; lower score is better):

| | Combined_V1 | PairTrading | Cash | Combined_V1 place |
|---|---|---|---|---|
| all windows | **2.99** | 3.42 | 3.20 | **1st** |
| 2024-25 | **3.05** | 3.30 | 3.54 | **1st** |
| 2022-23 | 2.92 | 3.54 | 2.88 | 2nd (just behind Cash) |
| team table (4 agents) | **1.91** | 2.30 | n/a | 1st |
| metrics rounded to 4 or 6 decimals | 2.97 / 2.92 | 3.11 / 3.32 | 3.54 / 3.37 | 1st |
| whole shares only | 3.40 | 3.42 | 3.40 | ties Cash |
| 1-cent minimum fee per order | 3.57 | 4.10 | 2.80 | 2nd |

**Caveats.** Combined_V1 makes about 0% (0.004% over 2022-2025). It ranks well because of how the score is built,
not because it earns anything. It relies on fractional shares and proportional fees, both of which fit the web
run. It would lose its edge if a rival held even less, if the organisers add a return threshold, or if they rank
differently in the official round.


`strategies/BreadthGuard_v2.py` is the updated strategy (entry point `strategy`). `strategies/BreadthGuard_v1.py`
is the previous version; the two teammates' strategies are in `strategies/` for the comparisons.

## Official competition alignment (checked against the ICAIF 2026 starter kit)

| Official rule (kit `docs/`) | Combined_V1 |
|---|---|
| Score = mean of ranks on cumulative return, Sharpe (per-round, x42), max drawdown (period ends + daily closes), turnover; exact values, shared ties | Same four metrics are what the replica ranks (`backtest/field2.py`) |
| Long-only, each weight 0-0.30, sum <= 1, all 30 symbols | Yes. Every upload passes the kit's own `validate_payload` (`kit_tests/test_kit.py`) |
| Fractional shares allowed; fee 0.1% of notional, no minimum | These are the two assumptions the near-cash design needs. Both are confirmed |
| Missing decision = hold, no trade, no fee | `run_combined_v1.py` uploads only when the agent trades (about 1-3 times per 105 rounds) |
| `watch` calls `strategy(observation)` and needs 30 weights every round | Fixed: the old `None` (hold) would have stopped `watch`. `kit_strategy` re-submits the last target instead |
| No price feed in the kit; public data only, disclosed | Daily closes from Yahoo Finance (completed closes before the decision day). Earnings misses are refreshed daily from Yahoo |

**Against a whole competition field, not just your team** (`backtest/field3.py`: three random 48-team fields with
cash teams, near-cash teams and 40 generic agents at 5-100% exposure, 65 windows):

| Agent | avg finishing position (of 48) | top-3 finishes |
|---|---|---|
| **Combined_V1** | **5.3** | 41% |
| PairTrading V5.1 | 7.1 | 38% |
| BreadthGuard v2 | 12.5 | 13% |
| jimin_test_v5 | 15.8 | 4% |
| an all-cash team | about 11.5 | n/a |

Higher sleeves (0.01%-5%) all finish worse, so the 0.001% sleeve stays. Run in the kit:
`python run_combined_v1.py --phase validation --once` (Validation, Oct 8-9), then
`python run_combined_v1.py --phase official` (Oct 12-30).

## BreadthGuard v2: what changed from v1

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
python3 comp.py && python3 comp_eval.py configs/cfg4.json   # v2 parameter sweeps
python3 calib.py                      # which metrics the web scorer ranks
python3 field2.py                     # calibrated field (10 bp fees; stress scenarios A/C)
python3 lab3.py configs/m4.json B     # Combined_V1 candidate sweeps
python3 final3.py                     # Combined_V1 final test -> results_combined_v1.md
```

Replica assumptions: one Round-1 decision per day, filled at the open; 2 bp cost; marks every hour where Yahoo has
hourly bars (from Nov 2023), open and close before that; stability = mean / std of mark-to-mark returns. These are
inferred from the screenshots, not taken from the official evaluator.
