# Combined_V5 - test results

Evaluator `field5.py`: 10 bp fees, fractional shares, Rounds 2-7 simulated where hourly bars exist (2023-10 on). Score = mean of the ranks of return, Sharpe (stability), max drawdown and turnover (lower is better). The field mimics past competitions: cash / near-cash teams, 30-100% equal-weight books, momentum, mean reversion, volatility targeting, an every-round rebalancer, the kit benchmarks and our own agents.


## 65 rolling 15-day windows, 2022-02 .. 2025-12

### Teams that hold a real portfolio

|                               |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:------------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Combined_V5                   |       4.565 |       2.738 |       25 |      0.085 |    0.389 |     0.001 |
| BreadthGuard v2               |       4.896 |       3.477 |       21 |      0.166 |    0.733 |     0.002 |
| Combined_V3                   |       5.519 |       4.554 |       17 |      0.157 |    0.703 |     0.002 |
| jimin_test_v5                 |       5.65  |       4.4   |        3 |      0.244 |    0.982 |     0.003 |
| EW 30% buy & hold             |       6.673 |       5.385 |        7 |      0.274 |    1.157 |     0.003 |
| Momentum top15 60%            |       7.129 |       6.954 |        3 |      0.674 |    2.436 |     0.007 |
| EW 60% buy & hold             |       7.421 |       6.954 |        2 |      0.548 |    2.302 |     0.006 |
| Vol-target EW 10%             |       7.802 |       7.585 |        4 |      0.537 |    2.497 |     0.008 |
| Vol-target EW 15%             |       8.156 |       8.292 |        1 |      0.713 |    3.154 |     0.009 |
| Equal weight, buy & hold      |       8.392 |       8.585 |        2 |      0.914 |    3.809 |     0.01  |
| EW 100% every-round rebalance |       9.146 |      10.169 |        1 |      0.866 |    3.834 |     0.012 |
| Momentum top10 100%           |       9.477 |      10.262 |        0 |      1.141 |    4.512 |     0.022 |
| Mean reversion 5d 60%         |      10.904 |      11.538 |        1 |     -0.196 |    3.334 |     0.057 |
| Kit example (recent winners)  |      11.958 |      12.492 |        0 |     -0.414 |    5.53  |     0.063 |
| Buy yesterday's losers        |      12.312 |      13.077 |        0 |     -0.666 |    5.816 |     0.225 |


### Whole field (incl. cash and near-cash teams)

|                               |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:------------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Combined_V4                   |       6.154 |       2.662 |       24 |      0     |    0     |     0     |
| PairTrading V5.1              |       7.358 |       6.246 |       12 |      0.001 |    0.003 |     0     |
| Cash only                     |       7.373 |       7.138 |       16 |      0     |    0     |     0     |
| Near-cash EW 2e-05            |       7.769 |       4.523 |       12 |      0     |    0     |     0     |
| Combined_V5                   |       7.908 |       6.123 |        0 |      0.085 |    0.389 |     0.001 |
| BreadthGuard v2               |       8.242 |       7.277 |        4 |      0.166 |    0.733 |     0.002 |
| Near-cash EW 2e-04            |       8.327 |       6     |        4 |      0     |    0.001 |     0     |
| Combined_V3                   |       8.965 |       8.662 |        1 |      0.157 |    0.703 |     0.002 |
| jimin_test_v5                 |       8.969 |       8.015 |        1 |      0.244 |    0.982 |     0.003 |
| EW 30% buy & hold             |      10.035 |       9.462 |        0 |      0.274 |    1.157 |     0.003 |
| Momentum top15 60%            |      10.575 |      10.908 |        2 |      0.674 |    2.436 |     0.007 |
| EW 60% buy & hold             |      10.783 |      11.092 |        0 |      0.548 |    2.302 |     0.006 |
| Vol-target EW 10%             |      11.294 |      11.846 |        0 |      0.537 |    2.497 |     0.008 |
| Vol-target EW 15%             |      11.563 |      12.492 |        0 |      0.713 |    3.154 |     0.009 |
| Equal weight, buy & hold      |      11.75  |      12.785 |        0 |      0.914 |    3.809 |     0.01  |
| EW 100% every-round rebalance |      12.577 |      14.246 |        0 |      0.866 |    3.834 |     0.012 |
| Momentum top10 100%           |      12.992 |      14.631 |        0 |      1.141 |    4.512 |     0.022 |
| Mean reversion 5d 60%         |      14.892 |      16.185 |        0 |     -0.196 |    3.334 |     0.057 |
| Kit example (recent winners)  |      16.096 |      17.046 |        0 |     -0.414 |    5.53  |     0.063 |
| Buy yesterday's losers        |      16.377 |      17.8   |        0 |     -0.666 |    5.816 |     0.225 |


Per-metric average ranks among real-portfolio teams:

|                    |   return |   stability |   maxdd |   trading |   score |   ret% |
|:-------------------|---------:|------------:|--------:|----------:|--------:|-------:|
| Combined_V5        |    9.538 |       6.185 |   1.062 |     1.477 |   4.565 |  0.085 |
| BreadthGuard v2    |    8.908 |       6.077 |   2.369 |     2.231 |   4.896 |  0.166 |
| Combined_V3        |    8.954 |       7.123 |   2.708 |     3.292 |   5.519 |  0.157 |
| jimin_test_v5      |    8.323 |       6.277 |   4.092 |     3.908 |   5.65  |  0.244 |
| EW 30% buy & hold  |    8.492 |       9.138 |   4.846 |     4.215 |   6.673 |  0.274 |
| Momentum top15 60% |    6.631 |       6.985 |   7.646 |     7.254 |   7.129 |  0.674 |

## Earnings-season windows (from Oct 12, 2022-2025 - the Official phase slot)

### Teams that hold a real portfolio

|                               |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:------------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Combined_V5                   |       4.562 |        1.75 |        2 |      0.184 |    0.393 |     0.002 |
| BreadthGuard v2               |       4.625 |        1.5  |        3 |      0.678 |    0.592 |     0.002 |
| Combined_V3                   |       5.438 |        3.25 |        0 |      0.628 |    0.644 |     0.002 |
| jimin_test_v5                 |       5.812 |        3.75 |        0 |      0.709 |    0.861 |     0.003 |
| EW 30% buy & hold             |       7.125 |        6.25 |        0 |      0.554 |    1.011 |     0.003 |
| Momentum top15 60%            |       7.625 |        8.5  |        0 |      1.087 |    2.394 |     0.006 |
| EW 60% buy & hold             |       7.812 |        7.75 |        0 |      1.107 |    2.014 |     0.006 |
| Vol-target EW 10%             |       8.5   |        8.5  |        0 |      0.415 |    2.535 |     0.008 |
| Equal weight, buy & hold      |       8.938 |       10    |        0 |      1.845 |    3.339 |     0.01  |
| Vol-target EW 15%             |       9.125 |       10.5  |        0 |      0.779 |    3.066 |     0.009 |
| EW 100% every-round rebalance |       9.438 |       11    |        0 |      1.821 |    3.331 |     0.012 |
| Mean reversion 5d 60%         |       9.5   |       10    |        0 |      0.989 |    2.324 |     0.06  |
| Buy yesterday's losers        |      10     |       11    |        0 |      2.197 |    4.855 |     0.226 |
| Momentum top10 100%           |      10.688 |       12.5  |        0 |      0.897 |    4.718 |     0.02  |
| Kit example (recent winners)  |      10.812 |       10.5  |        0 |      0.834 |    5.504 |     0.057 |


### Whole field (incl. cash and near-cash teams)

|                               |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:------------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Combined_V4                   |       5.625 |        2    |        1 |      0     |    0     |     0     |
| Cash only                     |       5.75  |        5.5  |        2 |      0     |    0     |     0     |
| PairTrading V5.1              |       7.188 |        3.75 |        0 |      0.005 |    0.002 |     0     |
| Near-cash EW 2e-05            |       7.812 |        5.25 |        0 |      0     |    0     |     0     |
| Combined_V5                   |       8.25  |        5    |        0 |      0.184 |    0.393 |     0.002 |
| BreadthGuard v2               |       8.375 |        4.5  |        1 |      0.678 |    0.592 |     0.002 |
| Near-cash EW 2e-04            |       8.5   |        7    |        0 |      0     |    0.001 |     0     |
| Combined_V3                   |       9.062 |        7    |        0 |      0.628 |    0.644 |     0.002 |
| jimin_test_v5                 |       9.375 |        7.25 |        0 |      0.709 |    0.861 |     0.003 |
| EW 30% buy & hold             |      10.75  |       11.25 |        0 |      0.554 |    1.011 |     0.003 |
| Momentum top15 60%            |      11.312 |       12.75 |        0 |      1.087 |    2.394 |     0.006 |
| EW 60% buy & hold             |      11.438 |       13    |        0 |      1.107 |    2.014 |     0.006 |
| Vol-target EW 10%             |      12.25  |       13.25 |        0 |      0.415 |    2.535 |     0.008 |
| Equal weight, buy & hold      |      12.5   |       15    |        0 |      1.845 |    3.339 |     0.01  |
| Vol-target EW 15%             |      12.688 |       15.5  |        0 |      0.779 |    3.066 |     0.009 |
| EW 100% every-round rebalance |      13.125 |       16.25 |        0 |      1.821 |    3.331 |     0.012 |
| Mean reversion 5d 60%         |      13.25  |       15.25 |        0 |      0.989 |    2.324 |     0.06  |
| Buy yesterday's losers        |      13.625 |       14.75 |        0 |      2.197 |    4.855 |     0.226 |
| Kit example (recent winners)  |      14.562 |       14    |        0 |      0.834 |    5.504 |     0.057 |
| Momentum top10 100%           |      14.562 |       17.5  |        0 |      0.897 |    4.718 |     0.02  |


Per-metric average ranks among real-portfolio teams:

|                    |   return |   stability |   maxdd |   trading |   score |   ret% |
|:-------------------|---------:|------------:|--------:|----------:|--------:|-------:|
| Combined_V5        |     8.25 |        6.75 |    1.25 |      2    |   4.562 |  0.184 |
| BreadthGuard v2    |     7.75 |        7    |    1.75 |      2    |   4.625 |  0.678 |
| Combined_V3        |     9    |        7    |    3    |      2.75 |   5.438 |  0.628 |
| jimin_test_v5      |     8    |        6.25 |    4.25 |      4.75 |   5.812 |  0.709 |
| EW 30% buy & hold  |     8.75 |       11    |    4.75 |      4    |   7.125 |  0.554 |
| Momentum top15 60% |     8.75 |        7.5  |    7.5  |      6.75 |   7.625 |  1.087 |


## Size

Stock sleeve after each V5 trade: median 11.3%, 10th-90th pct 4.7% - 15.3%, max 39.8%.


## Whole period in one run (2022-02-01 .. 2025-12-31)

return 6.48%, max drawdown 2.34%, traded notional 1.63x NAV over 983 days.

