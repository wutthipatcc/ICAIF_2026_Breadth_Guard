# BreadthGuard v1 vs v2 - replica evaluator results

65 windows x 15 trading days, 2022-02-01 .. 2025-12-31, fills at the open, 2 bp cost unless noted, hourly marks from 2023-11 (open/close before). v1 A/B mode in the v2 file matches v1 (max return diff 0.0e+00).


## Team table with BreadthGuard v1

|                  |   avg_score |   avg_place |   firsts |   avg_ret% |   win_vs_cash |   avg_dd% |
|:-----------------|------------:|------------:|---------:|-----------:|--------------:|----------:|
| PairTrading V5.1 |       1.612 |       1.246 |       49 |      0.001 |         0.769 |     0.003 |
| jimin_test_v5    |       2.108 |       1.923 |       24 |      0.268 |         0.754 |     0.977 |
| BreadthGuard v1  |       2.281 |       2.246 |       15 |      0.276 |         0.754 |     1.001 |


## Mock competition with benchmarks - BreadthGuard v1

|                              |   avg_score |   avg_place |   firsts |   avg_ret% |   win_vs_cash |   avg_dd% |
|:-----------------------------|------------:|------------:|---------:|-----------:|--------------:|----------:|
| PairTrading V5.1             |       2.958 |       2.031 |       28 |      0.001 |         0.769 |     0.003 |
| Cash only                    |       3.069 |       2.954 |       19 |      0     |         0     |     0     |
| jimin_test_v5                |       3.415 |       2.477 |       23 |      0.268 |         0.754 |     0.977 |
| BreadthGuard v1              |       3.581 |       3.046 |       14 |      0.276 |         0.754 |     1.001 |
| Equal weight, buy & hold     |       4.423 |       4.508 |        5 |      0.994 |         0.692 |     3.793 |
| Kit example (recent winners) |       5.096 |       5.262 |        3 |      1.429 |         0.585 |     4.846 |
| Buy yesterday's losers       |       5.458 |       5.985 |        0 |      0.277 |         0.569 |     5.458 |


## Team table with BreadthGuard v2

|                  |   avg_score |   avg_place |   firsts |   avg_ret% |   win_vs_cash |   avg_dd% |
|:-----------------|------------:|------------:|---------:|-----------:|--------------:|----------:|
| PairTrading V5.1 |       1.619 |       1.169 |       54 |      0.001 |         0.769 |     0.003 |
| BreadthGuard v2  |       1.977 |       1.723 |       25 |      0.183 |         0.754 |     0.728 |
| jimin_test_v5    |       2.404 |       2.415 |       12 |      0.268 |         0.754 |     0.977 |


## Mock competition with benchmarks - BreadthGuard v2

|                              |   avg_score |   avg_place |   firsts |   avg_ret% |   win_vs_cash |   avg_dd% |
|:-----------------------------|------------:|------------:|---------:|-----------:|--------------:|----------:|
| PairTrading V5.1             |       2.965 |       1.877 |       31 |      0.001 |         0.769 |     0.003 |
| Cash only                    |       3.069 |       2.969 |       20 |      0     |         0     |     0     |
| BreadthGuard v2              |       3.285 |       2.431 |       16 |      0.183 |         0.754 |     0.728 |
| jimin_test_v5                |       3.712 |       3.092 |        6 |      0.268 |         0.754 |     0.977 |
| Equal weight, buy & hold     |       4.412 |       4.369 |        8 |      0.994 |         0.692 |     3.793 |
| Kit example (recent winners) |       5.096 |       5.277 |        3 |      1.429 |         0.585 |     4.846 |
| Buy yesterday's losers       |       5.462 |       5.969 |        2 |      0.277 |         0.569 |     5.458 |


## Mock competition - micro variant instead of v2

|                              |   avg_score |   avg_place |   firsts |   avg_ret% |   win_vs_cash |   avg_dd% |
|:-----------------------------|------------:|------------:|---------:|-----------:|--------------:|----------:|
| BreadthGuard v2 micro        |       2.95  |       1.708 |       31 |      0     |         0.754 |     0     |
| Cash only                    |       3.069 |       2.923 |       19 |      0     |         0     |     0     |
| PairTrading V5.1             |       3.338 |       2.708 |       22 |      0.001 |         0.769 |     0.003 |
| jimin_test_v5                |       3.704 |       3.123 |        8 |      0.268 |         0.754 |     0.977 |
| Equal weight, buy & hold     |       4.408 |       4.385 |        6 |      0.994 |         0.692 |     3.793 |
| Kit example (recent winners) |       5.085 |       5.246 |        4 |      1.429 |         0.585 |     4.846 |
| Buy yesterday's losers       |       5.446 |       5.969 |        1 |      0.277 |         0.569 |     5.458 |


## Robustness: avg score of BreadthGuard vs Cash in the 7-entrant field

| scenario                         | strategy              |   score |   cash score |   place of 7 |
|:---------------------------------|:----------------------|--------:|-------------:|-------------:|
| base (2bp, equal metric weights) | BreadthGuard v1       |   3.581 |        3.069 |            4 |
| base (2bp, equal metric weights) | BreadthGuard v2       |   3.285 |        3.069 |            3 |
| base (2bp, equal metric weights) | BreadthGuard v2 micro |   2.95  |        3.069 |            1 |
| metric weights 0.6/0.6/1/1       | BreadthGuard v1       |   3.603 |        2.552 |            4 |
| metric weights 0.6/0.6/1/1       | BreadthGuard v2       |   3.225 |        2.552 |            3 |
| metric weights 0.6/0.6/1/1       | BreadthGuard v2 micro |   2.712 |        2.552 |            2 |
| stability = Sortino              | BreadthGuard v1       |   3.573 |        3.069 |            4 |
| stability = Sortino              | BreadthGuard v2       |   3.288 |        3.069 |            3 |
| stability = Sortino              | BreadthGuard v2 micro |   2.958 |        3.069 |            1 |
| 2022-02 .. 2023-12 windows       | BreadthGuard v1       |   3.568 |        2.735 |            4 |
| 2022-02 .. 2023-12 windows       | BreadthGuard v2       |   3.288 |        2.735 |            3 |
| 2022-02 .. 2023-12 windows       | BreadthGuard v2 micro |   2.856 |        2.735 |            2 |
| 2024-01 .. 2025-12 windows       | BreadthGuard v1       |   3.594 |        3.414 |            4 |
| 2024-01 .. 2025-12 windows       | BreadthGuard v2       |   3.281 |        3.414 |            2 |
| 2024-01 .. 2025-12 windows       | BreadthGuard v2 micro |   3.047 |        3.414 |            1 |
| cost 0 bp                        | BreadthGuard v1       |   3.6   |        3.088 |            4 |
| cost 0 bp                        | BreadthGuard v2       |   3.323 |        3.088 |            3 |
| cost 0 bp                        | BreadthGuard v2 micro |   2.973 |        3.088 |            1 |
| cost 5 bp                        | BreadthGuard v1       |   3.523 |        3.031 |            4 |
| cost 5 bp                        | BreadthGuard v2       |   3.254 |        3.031 |            3 |
| cost 5 bp                        | BreadthGuard v2 micro |   2.919 |        3.031 |            1 |


## Whole period in one run (2022-02-01 .. 2025-12-31)

|                                     |   return % |   stability |   max DD % |   vol per mark |
|:------------------------------------|-----------:|------------:|-----------:|---------------:|
| jimin_test_v5                       |    17.2057 |      0.029  |     5.4474 |         0.0011 |
| BreadthGuard v1                     |    24.1249 |      0.0263 |     8.9538 |         0.0017 |
| BreadthGuard v1 (v2 file, A/B mode) |    24.1249 |      0.0263 |     8.9538 |         0.0017 |
| BreadthGuard v2                     |    28.0019 |      0.0302 |     8.0089 |         0.0016 |
| Cash only                           |     0      |      0      |     0      |         0      |
| Equal weight, buy & hold            |    90.3357 |      0.0275 |    23.5775 |         0.005  |
| PairTrading V5.1                    |     0.7564 |      0.0326 |     0.2128 |         0      |
| Buy yesterday's losers              |    11.2379 |      0.0065 |    34.2193 |         0.0072 |
| Kit example (recent winners)        |   132.552  |      0.0293 |    23.5464 |         0.0063 |
| BreadthGuard v2 micro               |     0.0017 |      0.0304 |     0.0005 |         0      |
