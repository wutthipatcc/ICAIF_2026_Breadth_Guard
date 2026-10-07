# Combined_V5 - test results

Evaluator `field5.py`: 10 bp fees, fractional shares, Rounds 2-7 simulated where hourly bars exist (2023-10 on). Score = mean of the ranks of return, Sharpe (stability), max drawdown and turnover (lower is better). The field mimics past competitions: cash / near-cash teams, 30-100% equal-weight books, momentum, mean reversion, volatility targeting, an every-round rebalancer, the kit benchmarks and our own agents.


## 65 rolling 15-day windows, 2022-02 .. 2025-12

### Teams that hold a real portfolio

|                               |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:------------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Combined_V5                   |       4.492 |       2.508 |       28 |      0.092 |    0.389 |     0.001 |
| BreadthGuard v2               |       4.946 |       3.646 |       19 |      0.166 |    0.733 |     0.002 |
| Combined_V3                   |       5.523 |       4.646 |       13 |      0.157 |    0.703 |     0.002 |
| jimin_test_v5                 |       5.658 |       4.477 |        4 |      0.244 |    0.982 |     0.003 |
| EW 30% buy & hold             |       6.665 |       5.338 |        7 |      0.274 |    1.157 |     0.003 |
| Momentum top15 60%            |       7.129 |       6.938 |        3 |      0.674 |    2.436 |     0.007 |
| EW 60% buy & hold             |       7.421 |       6.985 |        2 |      0.548 |    2.302 |     0.006 |
| Vol-target EW 10%             |       7.798 |       7.538 |        4 |      0.537 |    2.497 |     0.008 |
| Vol-target EW 15%             |       8.16  |       8.308 |        1 |      0.713 |    3.154 |     0.009 |
| Equal weight, buy & hold      |       8.388 |       8.6   |        2 |      0.914 |    3.809 |     0.01  |
| EW 100% every-round rebalance |       9.15  |      10.185 |        1 |      0.866 |    3.834 |     0.012 |
| Momentum top10 100%           |       9.485 |      10.308 |        0 |      1.141 |    4.512 |     0.022 |
| Mean reversion 5d 60%         |      10.908 |      11.569 |        1 |     -0.196 |    3.334 |     0.057 |
| Kit example (recent winners)  |      11.962 |      12.477 |        0 |     -0.414 |    5.53  |     0.063 |
| Buy yesterday's losers        |      12.315 |      13.077 |        0 |     -0.666 |    5.816 |     0.225 |


### Whole field (incl. cash and near-cash teams)

|                               |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:------------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Combined_V4                   |       6.169 |       2.738 |       23 |      0     |    0     |     0     |
| PairTrading V5.1              |       7.358 |       6.2   |       13 |      0.001 |    0.003 |     0     |
| Cash only                     |       7.373 |       7.246 |       16 |      0     |    0     |     0     |
| Near-cash EW 2e-05            |       7.765 |       4.569 |       12 |      0     |    0     |     0     |
| Combined_V5                   |       7.827 |       5.815 |        1 |      0.092 |    0.389 |     0.001 |
| BreadthGuard v2               |       8.292 |       7.4   |        3 |      0.166 |    0.733 |     0.002 |
| Near-cash EW 2e-04            |       8.323 |       5.985 |        4 |      0     |    0.001 |     0     |
| Combined_V3                   |       8.969 |       8.631 |        1 |      0.157 |    0.703 |     0.002 |
| jimin_test_v5                 |       8.977 |       7.969 |        1 |      0.244 |    0.982 |     0.003 |
| EW 30% buy & hold             |      10.027 |       9.369 |        0 |      0.274 |    1.157 |     0.003 |
| Momentum top15 60%            |      10.575 |      10.862 |        2 |      0.674 |    2.436 |     0.007 |
| EW 60% buy & hold             |      10.783 |      11.077 |        0 |      0.548 |    2.302 |     0.006 |
| Vol-target EW 10%             |      11.29  |      11.815 |        0 |      0.537 |    2.497 |     0.008 |
| Vol-target EW 15%             |      11.567 |      12.508 |        0 |      0.713 |    3.154 |     0.009 |
| Equal weight, buy & hold      |      11.746 |      12.785 |        0 |      0.914 |    3.809 |     0.01  |
| EW 100% every-round rebalance |      12.581 |      14.231 |        0 |      0.866 |    3.834 |     0.012 |
| Momentum top10 100%           |      13     |      14.615 |        0 |      1.141 |    4.512 |     0.022 |
| Mean reversion 5d 60%         |      14.896 |      16.215 |        0 |     -0.196 |    3.334 |     0.057 |
| Kit example (recent winners)  |      16.1   |      17.046 |        0 |     -0.414 |    5.53  |     0.063 |
| Buy yesterday's losers        |      16.381 |      17.785 |        0 |     -0.666 |    5.816 |     0.225 |


Per-metric average ranks among real-portfolio teams:

|                    |   return |   stability |   maxdd |   trading |   score |   ret% |
|:-------------------|---------:|------------:|--------:|----------:|--------:|-------:|
| Combined_V5        |    9.6   |       6.046 |   1.062 |     1.262 |   4.492 |  0.092 |
| BreadthGuard v2    |    8.877 |       6.108 |   2.369 |     2.431 |   4.946 |  0.166 |
| Combined_V3        |    8.938 |       7.138 |   2.708 |     3.308 |   5.523 |  0.157 |
| jimin_test_v5      |    8.338 |       6.292 |   4.092 |     3.908 |   5.658 |  0.244 |
| EW 30% buy & hold  |    8.477 |       9.123 |   4.846 |     4.215 |   6.665 |  0.274 |
| Momentum top15 60% |    6.631 |       6.985 |   7.646 |     7.254 |   7.129 |  0.674 |

## Earnings-season windows (from Oct 12, 2022-2025 - the Official phase slot)

### Teams that hold a real portfolio

|                               |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:------------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Combined_V5                   |       4.25  |        1.5  |        2 |      0.205 |    0.39  |     0.002 |
| BreadthGuard v2               |       4.812 |        1.75 |        2 |      0.678 |    0.592 |     0.002 |
| Combined_V3                   |       5.438 |        3.25 |        0 |      0.628 |    0.644 |     0.002 |
| jimin_test_v5                 |       5.875 |        3.75 |        0 |      0.709 |    0.861 |     0.003 |
| EW 30% buy & hold             |       7.125 |        6    |        0 |      0.554 |    1.011 |     0.003 |
| Momentum top15 60%            |       7.625 |        8.5  |        0 |      1.087 |    2.394 |     0.006 |
| EW 60% buy & hold             |       7.812 |        7.75 |        0 |      1.107 |    2.014 |     0.006 |
| Vol-target EW 10%             |       8.5   |        8.5  |        0 |      0.415 |    2.535 |     0.008 |
| Equal weight, buy & hold      |       8.938 |       10    |        0 |      1.845 |    3.339 |     0.01  |
| Vol-target EW 15%             |       9.125 |       10.5  |        0 |      0.779 |    3.066 |     0.009 |
| EW 100% every-round rebalance |       9.438 |       10.75 |        0 |      1.821 |    3.331 |     0.012 |
| Mean reversion 5d 60%         |       9.5   |       10    |        0 |      0.989 |    2.324 |     0.06  |
| Buy yesterday's losers        |      10     |       11    |        0 |      2.197 |    4.855 |     0.226 |
| Momentum top10 100%           |      10.688 |       12.5  |        0 |      0.897 |    4.718 |     0.02  |
| Kit example (recent winners)  |      10.875 |       10.5  |        0 |      0.834 |    5.504 |     0.057 |


### Whole field (incl. cash and near-cash teams)

|                               |   avg_score |   avg_place |   firsts |   avg_ret% |   maxdd% |   trading |
|:------------------------------|------------:|------------:|---------:|-----------:|---------:|----------:|
| Cash only                     |       5.75  |        5.5  |        2 |      0     |    0     |     0     |
| Combined_V4                   |       5.812 |        2    |        1 |      0     |    0     |     0     |
| PairTrading V5.1              |       7.188 |        4    |        0 |      0.005 |    0.002 |     0     |
| Combined_V5                   |       7.75  |        4    |        0 |      0.205 |    0.39  |     0.002 |
| Near-cash EW 2e-05            |       7.812 |        5.25 |        0 |      0     |    0     |     0     |
| Near-cash EW 2e-04            |       8.5   |        7    |        0 |      0     |    0.001 |     0     |
| BreadthGuard v2               |       8.562 |        5    |        1 |      0.678 |    0.592 |     0.002 |
| Combined_V3                   |       9.062 |        7    |        0 |      0.628 |    0.644 |     0.002 |
| jimin_test_v5                 |       9.438 |        7.5  |        0 |      0.709 |    0.861 |     0.003 |
| EW 30% buy & hold             |      10.75  |       11.5  |        0 |      0.554 |    1.011 |     0.003 |
| Momentum top15 60%            |      11.312 |       12.75 |        0 |      1.087 |    2.394 |     0.006 |
| EW 60% buy & hold             |      11.438 |       13    |        0 |      1.107 |    2.014 |     0.006 |
| Vol-target EW 10%             |      12.25  |       13.25 |        0 |      0.415 |    2.535 |     0.008 |
| Equal weight, buy & hold      |      12.5   |       15    |        0 |      1.845 |    3.339 |     0.01  |
| Vol-target EW 15%             |      12.688 |       15.5  |        0 |      0.779 |    3.066 |     0.009 |
| EW 100% every-round rebalance |      13.125 |       16.25 |        0 |      1.821 |    3.331 |     0.012 |
| Mean reversion 5d 60%         |      13.25  |       15.25 |        0 |      0.989 |    2.324 |     0.06  |
| Buy yesterday's losers        |      13.625 |       14.5  |        0 |      2.197 |    4.855 |     0.226 |
| Momentum top10 100%           |      14.562 |       17.5  |        0 |      0.897 |    4.718 |     0.02  |
| Kit example (recent winners)  |      14.625 |       14.5  |        0 |      0.834 |    5.504 |     0.057 |


Per-metric average ranks among real-portfolio teams:

|                    |   return |   stability |   maxdd |   trading |   score |   ret% |
|:-------------------|---------:|------------:|--------:|----------:|--------:|-------:|
| Combined_V5        |     8.25 |        6    |    1.25 |      1.5  |   4.25  |  0.205 |
| BreadthGuard v2    |     7.75 |        7.25 |    1.75 |      2.5  |   4.812 |  0.678 |
| Combined_V3        |     9    |        7    |    3    |      2.75 |   5.438 |  0.628 |
| jimin_test_v5      |     8    |        6.5  |    4.25 |      4.75 |   5.875 |  0.709 |
| EW 30% buy & hold  |     8.75 |       11    |    4.75 |      4    |   7.125 |  0.554 |
| Momentum top15 60% |     8.75 |        7.5  |    7.5  |      6.75 |   7.625 |  1.087 |


## Size

Stock sleeve after each V5 trade: median 11.3%, 10th-90th pct 4.7% - 15.3%, max 39.8%.


## Whole period in one run (2022-02-01 .. 2025-12-31)

return 6.48%, max drawdown 2.34%, traded notional 1.63x NAV over 983 days.

