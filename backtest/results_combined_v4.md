# Combined_V4 - test results

Evaluator `field4.py` (= `field2.py` calibration): 65 windows x 15 trading days, 2022-02-01 .. 2025-12-31, 10 bp fees, fractional shares, equal-weight ranks of return / stability / max drop / trading. The field is the 2026-10-07 web screenshot field; NemoV5 is a stand-in (its code is not in the repo) calibrated to its web row.


## 1. My strategies ranked against each other (65 three-week tests)

|                  |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |   rank return |   rank stability |   rank maxdd |   rank trading |
|:-----------------|------------:|------------:|---------:|-----------:|---------:|----------:|--------------:|-----------------:|-------------:|---------------:|
| Combined_V4      |       2.658 |       1.523 |       41 |      0     |    0     |     0     |         5.415 |            3.215 |        1     |          1     |
| PairTrading V5.1 |       3.204 |       2.662 |       24 |      0.001 |    0.003 |     0     |         4.877 |            3.938 |        2     |          2     |
| BreadthGuard v2  |       3.631 |       3.169 |       11 |      0.166 |    0.733 |     0.002 |         4.046 |            3.8   |        3.415 |          3.262 |
| Combined_V3      |       4.019 |       3.938 |        3 |      0.122 |    0.718 |     0.002 |         3.985 |            4.154 |        3.738 |          4.2   |
| jimin_test_v5    |       4.423 |       4.431 |        4 |      0.244 |    0.982 |     0.003 |         3.431 |            4.015 |        5.262 |          4.985 |
| BreadthGuard v1  |       4.615 |       5.062 |        1 |      0.251 |    1.007 |     0.003 |         3.262 |            4.062 |        5.585 |          5.554 |
| NemoV5 (proxy)   |       5.45  |       6.231 |        0 |      0.987 |    4.074 |     0.011 |         2.985 |            4.815 |        7     |          7     |


## 2. The whole period in one run (2022-02-01 .. 2025-12-31)

|                  |   score |     return% |   stability |      maxdd% |     trading |
|:-----------------|--------:|------------:|------------:|------------:|------------:|
| PairTrading V5.1 |     2.5 |  0.752349   |   0.032397  |  0.213031   | 5.09086e-05 |
| Combined_V4      |     2.5 |  0.00348948 |   0.031285  |  0.00106839 | 1.20553e-06 |
| jimin_test_v5    |     4   | 16.9873     |   0.0286243 |  5.47696    | 0.00237664  |
| BreadthGuard v2  |     4   | 27.5838     |   0.0297887 |  8.0206     | 0.00417601  |
| Combined_V3      |     5   | -2.72023    |  -0.0173281 |  3.09092    | 0.00076413  |
| BreadthGuard v1  |     5   | 23.7463     |   0.0259016 |  9.03952    | 0.0038951   |
| NemoV5 (proxy)   |     5   | 89.0489     |   0.026817  | 24.4723     | 0.0207258   |


## 3. Mock competition including benchmarks

|                              |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:-----------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Combined_V4                  |       3.712 |       1.831 |       28 |      0     |    0     |     0     |
| Cash only                    |       4.285 |       4.046 |       16 |      0     |    0     |     0     |
| PairTrading V5.1             |       4.327 |       3.462 |       20 |      0.001 |    0.003 |     0     |
| BreadthGuard v2              |       4.719 |       3.985 |        9 |      0.166 |    0.733 |     0.002 |
| Combined_V3                  |       5.165 |       4.785 |        3 |      0.122 |    0.718 |     0.002 |
| jimin_test_v5                |       5.512 |       4.969 |        5 |      0.244 |    0.982 |     0.003 |
| BreadthGuard v1              |       5.685 |       5.769 |        1 |      0.251 |    1.007 |     0.003 |
| Equal weight, buy & hold     |       6.788 |       7.262 |        1 |      0.914 |    3.809 |     0.01  |
| NemoV5 (proxy)               |       6.877 |       7.908 |        0 |      0.987 |    4.074 |     0.011 |
| Buy yesterday's losers       |       8.823 |       9.431 |        0 |     -0.666 |    5.816 |     0.225 |
| Kit example (recent winners) |      10.108 |      10.585 |        0 |     -5.844 |    8.688 |     0.063 |


## 4. Robustness (mock-competition field unless noted)

| scenario                          |   Combined_V4 |   PairTrading |   Cash |   V4 place |   of |
|:----------------------------------|--------------:|--------------:|-------:|-----------:|-----:|
| mock competition (main)           |         3.712 |         4.327 |  4.285 |          1 |   11 |
| 2022-02 .. 2023-12 windows        |         3.53  |         4.379 |  3.795 |          1 |   11 |
| 2024-01 .. 2025-12 windows        |         3.898 |         4.273 |  4.789 |          1 |   11 |
| volatility instead of trading     |         3.712 |         4.327 |  4.285 |          1 |   11 |
| 5 metrics (+volatility)           |         3.369 |         4.062 |  3.628 |          1 |   11 |
| metrics rounded to 6 decimals     |         3.64  |         4.227 |  4.456 |          1 |   11 |
| metrics rounded to 4 decimals     |         3.696 |         4.015 |  4.612 |          1 |   11 |
| + Combined_V1 in the field        |         3.992 |         5.008 |  4.685 |          1 |   12 |
| stress A: 10bp + 1c floor         |         5.223 |         5.162 |  3.723 |          5 |   11 |
| stress C: 10bp + 1c, whole shares |         4.477 |         4.481 |  4.477 |          1 |   11 |
