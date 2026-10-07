"""jimin_finhealth - fixed-basket, buy-once-and-hold agents built on jimin_bigtech7, tilted to Finance and Healthcare
(ICAIF 2026)

Same mechanics as jimin_bigtech7: buy the basket once at the first Round 1 and never submit again (hold), so the fee is
paid once and turnover = sleeve / 105.  No signals, no rebalancing, no LLM, no external data.

Baskets (equal weight inside each group, all 30 symbols submitted, the rest at 0):
  * strategy = tilt15        DEFAULT. Prioritise Finance + Healthcare: 2/3 of a 15% sleeve in the 10 Finance +
                              Healthcare names (JPM BAC GS V PYPL, LLY JNJ UNH PFE TMO; 1.0% each), 1/3 in big tech
                              without Tesla (AAPL MSFT NVDA GOOGL META AMZN; 0.83% each)
  * finhealth_tilt25 / tilt40 the same tilt at 25% / 40%
  * finhealth15 / 25 / 40     Finance + Healthcare only, 10 names
  * bigtech6                  jimin_bigtech7 without Tesla (6 names), 25% sleeve
Why: Finance and Healthcare are the least correlated groups with big tech (bank / pharma names average 0.13-0.21
correlation to the rest, BreadthGuard correlation review), so they diversify a big-tech-heavy field; Tesla is the most
volatile name in the universe (largest drawdown contributor at equal weight).
Backtest (backtest/basket_check.py -> backtest/results_finhealth.md; each agent alone vs a 20-team field of cash,
near-cash, equal-weight, momentum, mean-reversion and vol-target teams; lower score is better; rank among the 15
teams that hold a real portfolio):
                                   2022-25 (65 windows)   Oct 12 windows 2022-25   2026 Jan-Oct (12 windows)
  jimin_bigtech7 25%               6.24  #4               6.00  #4                 6.76  #5
  bigtech6 (no TSLA) 25%           6.20  #4               5.88  #4                 6.55  #5
  Fin+Health 10, 25%               6.24  #4               7.06  #5                 6.20  #4
  Fin+Health 10, 15%               5.66  #4               5.88  #4                 5.38  #2
  tilt 2/3 FH + 1/3 tech, 25%      5.76  #4               7.31  #5                 6.11  #4
  tilt 2/3 FH + 1/3 tech, 15%      5.10  #2               5.94  #4                 5.23  #2   <- default
  (Combined_V5 for reference       4.49  #1               4.25  #1                 4.79  #1)
The Finance + Healthcare tilt beats the big-tech basket in every period at the same or smaller size; the 15% size
beats 25% and 40%.  2026 to Oct 6: big tech +11.6%, Healthcare +15.9%, Finance +1.8% (Finance -5.9% in the last
20 days), so the Finance half is the weak spot right now.
"""
try:
    from testbed import zero_weights
except ImportError:                                   # official kit / standalone
    UNIVERSE = ["AAPL", "MSFT", "NVDA", "INTC", "CRM", "JPM", "BAC", "GS", "V", "PYPL", "LLY", "JNJ", "UNH", "PFE",
                "TMO", "AMZN", "TSLA", "WMT", "NKE", "KO", "CAT", "GE", "BA", "XOM", "CVX", "GOOGL", "META", "DIS", "T",
                "NEE"]

    def zero_weights():
        return {s: 0.0 for s in UNIVERSE}

NAME = "jimin_finhealth"
FINANCE = ["JPM", "BAC", "GS", "V", "PYPL"]
HEALTHCARE = ["LLY", "JNJ", "UNH", "PFE", "TMO"]
BIGTECH6 = ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN"]          # jimin_bigtech7 minus TSLA
EXPOSURE = 0.25
PER_NAME_CAP = 0.30


def _rule(observation, groups):
    """groups: list of (basket, share of the stock sleeve). Buy once at the first Round 1, then hold."""
    syms = observation["symbols"]
    port = observation["portfolio"]
    started = bool(port.get("positions")) or sum((port.get("weights") or {}).values()) > 0
    if started:
        return None                                  # bought once: hold to the end (no submission)
    if (observation.get("round") or {}).get("number", 1) != 1:
        return None                                  # first purchase only at Round 1
    out = zero_weights()
    for basket, share in groups:
        names = [s for s in syms if s in basket]
        if not names:
            continue
        w = min(share / len(names), PER_NAME_CAP)
        for s in names:
            out[s] += float(w)
    return out if sum(out.values()) > 0 else None


def _finhealth(exposure):
    return [(FINANCE + HEALTHCARE, exposure)]


def _tilt(exposure):
    return [(FINANCE + HEALTHCARE, exposure * 2 / 3), (BIGTECH6, exposure / 3)]


def finhealth25(observation): return _rule(observation, _finhealth(0.25))
def finhealth15(observation): return _rule(observation, _finhealth(0.15))
def finhealth40(observation): return _rule(observation, _finhealth(0.40))
def finhealth_tilt25(observation): return _rule(observation, _tilt(0.25))
def tilt15(observation): return _rule(observation, _tilt(0.15))
def tilt40(observation): return _rule(observation, _tilt(0.40))
def bigtech6(observation): return _rule(observation, [(BIGTECH6, 0.25)])


def strategy(observation):
    return tilt15(observation)


strategy.name = "2/3 finance + healthcare, 1/3 big tech ex-TSLA, 15% hold"
finhealth25.name = "finance + healthcare 10 equal weight, 25% hold"
finhealth15.name = "finance + healthcare 10 equal weight, 15% hold"
finhealth40.name = "finance + healthcare 10 equal weight, 40% hold"
finhealth_tilt25.name = "2/3 finance + healthcare, 1/3 big tech ex-TSLA, 25% hold"
tilt15.name = "2/3 finance + healthcare, 1/3 big tech ex-TSLA, 15% hold"
tilt40.name = "2/3 finance + healthcare, 1/3 big tech ex-TSLA, 40% hold"
bigtech6.name = "big tech 6 (no TSLA) equal weight, 25% hold"
