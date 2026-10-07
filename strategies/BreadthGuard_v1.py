"""BreadthGuard - V4.1 plus broad-shock confirmation

Preserves the successful V4.1 trading and stock-selection strategy. The only
new technical extension is a breadth guard on the existing -2% shock trigger:
the 25% -> 40% equity step-up occurs only when the universe decline is broad,
not when a few extreme single-stock drops pull down the equal-weight average.

Default confirmation:
  * equal-weight mean daily return <= -2%
  * at least 65% of the 30 stocks are down
  * median stock return <= -0.5%

All other V4.1 rules are unchanged. Use v4_1_control() and breadth_guard() for
A/B testing in the same runner.
"""

import numpy as np
import pandas as pd

from testbed import get_daily_close, zero_weights

NAME = "BreadthGuard"
MISS_DAYS = 15          # trading days to stay out after a miss
MISS_THR = -0.5         # EPS surprise (%) below which it counts as a miss

MISS_TABLE = {
    "AAPL": "20230203:-3.8",
    "AMZN": "20190726:-6.5 20191025:-7.1 20200501:-18.0 20211029:-30.9 20220429:-191.6 20220729:-273.3 20230203:-81.7",
    "BA": "20190424:-1.0 20191023:-31.4 20200129:-97.6 20200429:-14.3 20200729:-89.6 20210127:-826.0 20210429:-41.0 20211027:-299.0 20220126:-4731.9 20220427:-995.8 20220727:-246.3 20221026:-7213.3 20230125:-961.3 20230426:-20.9 20231025:-25.0 20240731:-44.2 20241023:-19.7 20250128:-56.1 20251029:-214.4 20260728:-141.5",
    "BAC": "20200415:-33.4 20220718:-2.1 20240112:-45.6 20240416:-1.8",
    "CAT": "20190128:-14.7 20190724:-9.4 20191023:-8.1 20200428:-4.5 20230131:-4.2 20241030:-3.4 20250430:-2.2 20250805:-3.7",
    "CRM": "20241204:-1.5",
    "CVX": "20190802:-2.8 20200731:-73.2 20210129:-111.4 20210430:-4.6 20220128:-18.0 20220429:-2.7 20230127:-4.8 20231027:-17.1 20240802:-14.9 20250131:-2.3",
    "DIS": "20190807:-22.4 20200506:-33.0 20211111:-23.4 20220512:-9.2 20221109:-46.9 20230511:-0.9",
    "GE": "20190131:-24.1 20200429:-38.0 20200729:-66.4 20210126:-6.3 20221025:-28.1",
    "GOOGL": "20190430:-5.0 20191029:-18.8 20200429:-3.4 20220427:-4.4 20220727:-5.0 20221026:-15.3 20230203:-11.9",
    "GS": "20191015:-1.8 20200115:-14.0 20200415:-7.4 20220118:-9.4 20230117:-42.4 20230719:-19.6 20231017:-1.0",
    "INTC": "20220729:-58.3 20230127:-50.5 20240802:-80.2 20241101:-1533.5 20250725:-1169.5",
    "JPM": "20190115:-9.5 20200714:-10.4 20220413:-2.9 20220714:-4.8 20240112:-15.7 20260113:-3.9",
    "LLY": "20201027:-10.0 20210427:-10.9 20210803:-1.0 20211026:-1.2 20220203:-0.7 20220804:-26.3 20230427:-6.3 20241030:-19.5 20250501:-3.4",
    "META": "20190425:-47.3 20190725:-50.8 20220203:-4.1 20220728:-3.4 20221027:-12.1 20230202:-21.5 20251030:-84.3 20260730:-14.4",
    "MSFT": "20220727:-2.7",
    "NEE": "20190125:-3.0 20200124:-2.5",
    "NKE": "20190628:-5.4 20200325:-2.7 20200626:-858.5 20230630:-2.3",
    "NVDA": "20220825:-1.5 20221117:-17.3",
    "PFE": "20200128:-4.5 20210202:-9.7",
    "PYPL": "20200507:-11.6 20220202:-1.0 20240430:-11.4 20260203:-4.4",
    "T": "20200422:-1.4 20240124:-3.2 20240724:-0.6 20250423:-0.9",
    "TMO": "20230726:-5.2",
    "TSLA": "20190131:-6.5 20190425:-209.6 20190725:-182.3 20210128:-23.9 20231019:-9.8 20240125:-3.5 20240424:-8.1 20240724:-16.1 20250130:-5.1 20250423:-34.9 20250724:-1.1 20251023:-10.5 20260723:-39.1",
    "UNH": "20250417:-1.3 20250729:-8.2",
    "WMT": "20200218:-3.8 20210218:-8.0 20220517:-12.1 20250821:-8.0",
    "XOM": "20190426:-24.5 20190802:-13.6 20200131:-9.6 20200731:-17.1 20220429:-7.0 20230728:-3.9 20231027:-3.8 20240426:-4.8",
}


def _parse_table():
    out = {}
    for t, s in MISS_TABLE.items():
        out[t] = sorted((pd.Timestamp(x.split(":")[0]), float(x.split(":")[1])) for x in s.split() if x)
    return out


_MISS = _parse_table()


def add_miss(ticker, yyyymmdd, surprise):
    """Register a new miss at runtime (effective day = first Round-1 day on which the report is public)."""
    _MISS.setdefault(ticker, []).append((pd.Timestamp(yyyymmdd), float(surprise)))
    _MISS[ticker].sort()


def _zscore(x):
    x = np.asarray(x, dtype=float)
    m, s = np.nanmean(x), np.nanstd(x)
    z = (x - m) / s if s > 0 else np.zeros_like(x)
    return np.clip(np.nan_to_num(z), -2.5, 2.5)


def _decision_day(observation, daily):
    """Calendar date of the current Round-1 decision. Prefer an explicit date in the observation; otherwise the next
    business day after the last completed daily close."""
    rnd = observation.get("round", {}) or {}
    for key in ("day", "date", "trading_day", "as_of", "deadline", "execution_time", "id"):
        v = rnd.get(key) if isinstance(rnd, dict) else None
        if v:
            try:
                s = str(v)
                if key == "id":
                    s = s.split("-r")[0].split("-", 1)[1]        # validation-YYYY-MM-DD-r1
                return pd.Timestamp(s[:10])
            except Exception:
                pass
    for key in ("as_of", "timestamp", "date", "day"):
        v = observation.get(key)
        if v:
            try:
                return pd.Timestamp(str(v)[:10])
            except Exception:
                pass
    last = pd.Timestamp(daily.index[-1]).normalize()
    return last + pd.offsets.BDay(1)


def _excluded(observation, daily, syms):
    """Boolean mask: stocks with a miss whose effective day is within the last MISS_DAYS trading days (inclusive of today)."""
    today = _decision_day(observation, daily)
    idx = pd.DatetimeIndex(daily.index).normalize()
    past = idx[idx < today]
    start = past[-(MISS_DAYS - 1)] if len(past) >= MISS_DAYS - 1 else (past[0] if len(past) else today)
    out = np.zeros(len(syms), dtype=bool)
    for j, t in enumerate(syms):
        for d, s in _MISS.get(t, []):
            if s < MISS_THR and start <= d <= today:
                out[j] = True
                break
    return out


SHOCK_DROP = -0.02        # previous-day equal-weight return (close-to-close) that counts as a shock

# V4.1 keeps the successful V4 exposure / execution engine, but improves the
# cross-sectional stock ranking.  The extra features only use completed daily closes.
OPEN_THETA = 0.0030       # slightly stronger tilt only on the first purchase
BASE_THETA = 0.0025       # unchanged V4 tilt after the portfolio has started


def _signal_v4(daily, n):
    """Exact V4 12-1 month momentum signal (control)."""
    if len(daily) < 253:
        return np.zeros(n)
    raw = daily.iloc[-22].values / daily.iloc[-253].values - 1
    return _zscore(raw)


def _signal_rank_tuned(daily, n):
    """V4.1 signal: mostly 12-1 momentum, with a small medium-term confirmation
    and downside-risk penalty.  Designed for the 15-day competition horizon while
    preserving the original V4 thesis and avoiding high-turnover short-term signals.
    """
    if len(daily) < 253:
        return np.zeros(n)

    px = daily.astype(float)

    # 12-1 month momentum: the proven V4 anchor.
    long_raw = px.iloc[-22].values / px.iloc[-253].values - 1.0
    z_long = _zscore(long_raw)

    # Medium-term confirmation: about 3 months, skipping the latest week to avoid
    # blindly chasing yesterday's winners / very short-term noise.
    med_raw = px.iloc[-6].values / px.iloc[-64].values - 1.0
    z_med = _zscore(med_raw)

    # Downside-volatility penalty over the last 42 trading days.  This is a small
    # risk-quality adjustment, not a separate low-volatility strategy.
    r = px.pct_change().iloc[-42:]
    dn = np.minimum(r.to_numpy(dtype=float), 0.0)
    downside = np.sqrt(np.nanmean(dn * dn, axis=0))
    z_down = _zscore(downside)

    combo = 0.70 * z_long + 0.20 * z_med - 0.10 * z_down
    return _zscore(combo)


def _shock_yesterday_v4(daily):
    """Exact V4/V4.1 shock trigger, retained as the A/B control."""
    if len(daily) < 2:
        return False
    r = daily.iloc[-1].values / daily.iloc[-2].values - 1
    r = r[np.isfinite(r)]
    return bool(len(r)) and float(np.mean(r)) <= SHOCK_DROP


def _shock_yesterday(daily):
    """Breadth-confirmed shock trigger.

    Keep the proven -2% equal-weight trigger, but only step from 25% to 40%
    exposure when the selloff is genuinely broad. This avoids treating one or
    two extreme idiosyncratic crashes as a market-wide shock.
    """
    if len(daily) < 2:
        return False
    r = daily.iloc[-1].values / daily.iloc[-2].values - 1.0
    r = r[np.isfinite(r)]
    if not len(r):
        return False
    if float(np.mean(r)) > SHOCK_DROP:
        return False
    if float(np.mean(r < 0.0)) < 0.65:
        return False
    if float(np.median(r)) > -0.005:
        return False
    return True


def _rule(observation, S0, S1=None, theta=BASE_THETA, k=0.5, g=0.05,
          miss_rule=True, signal_mode="rank_tuned", opening_theta=OPEN_THETA,
          shock_mode="breadth"):

    syms = observation["symbols"]
    n = len(syms)
    port = observation["portfolio"]
    started = bool(port.get("positions"))
    if started and observation["round"]["number"] != 1:
        return None                                       # hold between daily decisions

    daily = get_daily_close(observation, lookback=253).reindex(columns=syms)
    w = port.get("weights") or {}
    cur = np.array([float(w.get(s, 0.0)) for s in syms])

    switched = S1 is not None and started and cur.sum() > (S0 + S1) / 2
    if S1 is not None and started and not switched:
        fire = _shock_yesterday_v4(daily) if shock_mode == "v4" else _shock_yesterday(daily)
    else:
        fire = False
    S = S1 if (switched or fire) else S0

    if signal_mode == "v4":
        z = _signal_v4(daily, n)
        theta_now = theta
    else:
        z = _signal_rank_tuned(daily, n)
        # From cash, changing composition does not increase gross buy notional for
        # a fixed stock sleeve, so use a slightly stronger opening tilt.  Afterwards
        # revert to the original V4 tilt to protect turnover.
        theta_now = opening_theta if not started else theta

    target = np.clip(S / n + theta_now * z, 0.0, 0.30)
    if target.sum() > 0:
        target = target * (S / target.sum())

    excl = _excluded(observation, daily, syms) if miss_rule else np.zeros(n, dtype=bool)
    target[excl] = 0.0                                    # miss -> cash (no redistribution)

    if not started or fire:
        new = target                                      # first purchase / shock switch: go straight to target
    else:
        must_sell = bool((excl & (cur > 1e-4)).any())
        if np.abs(target - cur).sum() < g and not must_sell:
            return None                                   # inside the no-trade band
        new = cur + k * (target - cur)
        new[excl] = 0.0                                   # excluded stocks go to zero in one step

    new = np.clip(new, 0.0, 0.30)
    if new.sum() > 1:
        new = new / new.sum()
    out = zero_weights()
    out.update({s: float(v) for s, v in zip(syms, new)})
    return out


# -----------------------------------------------------------------------------
# A/B functions.  Keep the exact V4 control beside the candidate so the same
# 65-test evaluator can compare them without changing any other code.
# -----------------------------------------------------------------------------

def v4_baseline(observation):
    """Original V4 control."""
    return _rule(
        observation,
        S0=0.25,
        S1=0.40,
        signal_mode="v4",
        opening_theta=BASE_THETA,
        shock_mode="v4",
    )


def v4_1_control(observation):
    """Exact V4.1 rank-tuned control with the original mean-only shock trigger."""
    return _rule(
        observation,
        S0=0.25,
        S1=0.40,
        signal_mode="rank_tuned",
        opening_theta=OPEN_THETA,
        shock_mode="v4",
    )


def breadth_guard(observation):
    """V4.1 unchanged except for the breadth-confirmed shock trigger."""
    return _rule(
        observation,
        S0=0.25,
        S1=0.40,
        signal_mode="rank_tuned",
        opening_theta=OPEN_THETA,
        shock_mode="breadth",
    )


def sh25_60(observation):
    return _rule(observation, S0=0.25, S1=0.60, signal_mode="rank_tuned")


def sh25_40(observation):
    return breadth_guard(observation)


def sh15_40(observation):
    return _rule(observation, S0=0.15, S1=0.40, signal_mode="rank_tuned")


def sh40_80(observation):
    return _rule(observation, S0=0.40, S1=0.80, signal_mode="rank_tuned")


def v3_s25(observation):
    return _rule(observation, S0=0.25, signal_mode="rank_tuned")


def v3_s40(observation):
    return _rule(observation, S0=0.40, signal_mode="rank_tuned")


def v3_s15(observation):
    return _rule(observation, S0=0.15, signal_mode="rank_tuned")


def v3_s30(observation):
    return _rule(observation, S0=0.30, signal_mode="rank_tuned")


def strategy(observation):
    """Default entry point: V4.1 + breadth-confirmed 25% -> 40% shock step-up."""
    return breadth_guard(observation)


v4_baseline.name = "V4 control - S25->40 shock"
v4_1_control.name = "V4.1 control - mean-only shock"
breadth_guard.name = "BreadthGuard - V4.1 broad-shock confirmation"
sh25_60.name = "V4.1 S25->60 shock"
sh25_40.name = "V4.1 S25->40 shock"
sh15_40.name = "V4.1 S15->40 shock"
sh40_80.name = "V4.1 S40->80 shock"
v3_s25.name = "V4.1 S25 no shock"
v3_s40.name = "V4.1 S40 no shock"
v3_s15.name = "V4.1 S15 no shock"
v3_s30.name = "V4.1 S30 no shock"
strategy.name = "BreadthGuard"

if __name__ == "__main__":
    import sys
    if "--refresh" in sys.argv:                           # print fresh MISS_TABLE rows from yfinance (needs internet)
        import yfinance as yf
        for t in sorted(MISS_TABLE):
            e = yf.Ticker(t).get_earnings_dates(limit=12).reset_index()
            e.columns = ["dt", "eps_est", "eps_rep", "surprise"]
            e["dt"] = pd.to_datetime(e.dt, utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
            e = e.dropna(subset=["surprise"])
            e = e[e.surprise < MISS_THR]
            eff = np.where(e.dt.dt.hour < 9, e.dt.dt.normalize(), e.dt.dt.normalize() + pd.Timedelta(days=1))
            print(f'    "{t}": "' + " ".join(f"{pd.Timestamp(d).strftime('%Y%m%d')}:{s:.1f}" for d, s in zip(eff, e.surprise)) + '",')