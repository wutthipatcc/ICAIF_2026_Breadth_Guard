# BreadthGuard v3 (Sentinel) - test results

Evaluator `field2.py`: 65 windows x 15 days (2022-02-01 .. 2025-12-31), 10 bp fees, fractional shares, ranks of return / stability / max drop / trading, equal weights (calibrated to the 2026-10-07 web run).


## 1. My strategies ranked against each other (team table)

|                            |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:---------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| BreadthGuard v3 (Sentinel) |       1.912 |       1.169 |       57 |      0     |    0     |     0     |
| PairTrading V5.1           |       2.296 |       1.954 |       29 |      0.001 |    0.003 |     0     |
| BreadthGuard v2            |       2.692 |       2.615 |        6 |      0.166 |    0.733 |     0.002 |
| jimin_test_v5              |       3.1   |       3.292 |        0 |      0.244 |    0.982 |     0.003 |


## 2. Mock competition with benchmarks (v1 dropped, v3 added - 8 entrants)

|                              |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:-----------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| BreadthGuard v3 (Sentinel)   |       2.985 |       1.508 |       39 |      0     |    0     |     0     |
| Cash only                    |       3.204 |       2.862 |       19 |      0     |    0     |     0     |
| PairTrading V5.1             |       3.419 |       2.8   |       26 |      0.001 |    0.003 |     0     |
| BreadthGuard v2              |       3.781 |       3.4   |        5 |      0.166 |    0.733 |     0.002 |
| jimin_test_v5                |       4.188 |       3.938 |        1 |      0.244 |    0.982 |     0.003 |
| Equal weight, buy & hold     |       4.823 |       5.062 |        4 |      0.914 |    3.809 |     0.01  |
| Buy yesterday's losers       |       6.327 |       6.754 |        0 |     -0.666 |    5.816 |     0.225 |
| Kit example (recent winners) |       7.273 |       7.631 |        0 |     -5.844 |    8.688 |     0.063 |


## 3. Mock competition with everything (9 entrants)

|                              |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:-----------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| BreadthGuard v3 (Sentinel)   |       3.277 |       1.692 |       35 |      0     |    0     |     0     |
| Cash only                    |       3.581 |       3.308 |       19 |      0     |    0     |     0     |
| PairTrading V5.1             |       3.731 |       3.092 |       24 |      0.001 |    0.003 |     0     |
| BreadthGuard v2              |       4.062 |       3.585 |        9 |      0.166 |    0.733 |     0.002 |
| jimin_test_v5                |       4.612 |       4.231 |        7 |      0.244 |    0.982 |     0.003 |
| BreadthGuard v1              |       4.762 |       4.831 |        4 |      0.251 |    1.007 |     0.003 |
| Equal weight, buy & hold     |       5.577 |       6     |        2 |      0.914 |    3.809 |     0.01  |
| Buy yesterday's losers       |       7.177 |       7.723 |        0 |     -0.666 |    5.816 |     0.225 |
| Kit example (recent winners) |       8.223 |       8.631 |        0 |     -5.844 |    8.688 |     0.063 |


## 4. Robustness (8-entrant field: team + v3 + benchmarks)

| scenario                          |   v3 score |   PairTrading |   Cash |   v3 place |   of |
|:----------------------------------|-----------:|--------------:|-------:|-----------:|-----:|
| main (B, trading metric)          |      2.985 |         3.419 |  3.204 |          1 |    8 |
| 2022-02 .. 2023-12 windows        |      2.924 |         3.538 |  2.879 |          2 |    8 |
| 2024-01 .. 2025-12 windows        |      3.047 |         3.297 |  3.539 |          1 |    8 |
| volatility instead of trading     |      2.985 |         3.419 |  3.204 |          1 |    8 |
| 5 metrics (+vol)                  |      2.788 |         3.335 |  2.763 |          2 |    8 |
| metrics rounded to 6 decimals     |      2.923 |         3.319 |  3.365 |          1 |    8 |
| metrics rounded to 4 decimals     |      2.965 |         3.108 |  3.535 |          1 |    8 |
| stress A: 10bp + 1c floor         |      3.569 |         4.1   |  2.804 |          2 |    8 |
| stress C: 10bp + 1c, whole shares |      3.404 |         3.423 |  3.404 |          1 |    8 |


## 5. Whole period in one run

return 0.0041%  max drop 0.0018%  stability 0.0268  - it makes essentially nothing; it is built to rank, not to earn.

