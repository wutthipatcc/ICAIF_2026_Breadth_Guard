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


# -----------------------------------------------------------------------------
# V2 additions: correlation-aware base weights and a risk / regime exposure gate.
# -----------------------------------------------------------------------------

_CACHE = {}


def _cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def _min_var_weights(daily, win=126, shrink=0.5, cap=0.10, iters=300):
    key = ("mv", daily.index[-1], len(daily), win, shrink, cap)
    return _cached(key, lambda: _min_var_raw(daily, win, shrink, cap, iters))


def _min_var_raw(daily, win, shrink, cap, iters):
    """Long-only minimum-variance weights (sum 1, each <= cap) from the last `win` daily returns.

    The sample correlation matrix is shrunk toward its average off-diagonal value (constant-correlation
    target), which keeps the solution stable for 30 names. Solved by projected gradient descent.
    """
    r = daily.pct_change().iloc[-win:].to_numpy(dtype=float)
    r = np.where(np.isfinite(r), r, 0.0)
    n = r.shape[1]
    sd = r.std(0)
    sd = np.where(sd > 0, sd, np.nanmedian(sd[sd > 0]) if (sd > 0).any() else 1.0)
    C = np.corrcoef(r, rowvar=False)
    C = np.where(np.isfinite(C), C, 0.0)
    rho = (C.sum() - n) / (n * (n - 1))
    C = (1 - shrink) * C + shrink * (rho + (1 - rho) * np.eye(n))
    cov = C * np.outer(sd, sd)
    w = np.full(n, 1.0 / n)
    step = 0.5 / np.linalg.eigvalsh(cov)[-1]
    for _ in range(iters):
        w = _project_capped_simplex(w - step * (cov @ w), cap)
    return w


def _project_capped_simplex(v, cap):
    """Euclidean projection onto {w : sum w = 1, 0 <= w <= cap}: find the shift tau with
    sum(clip(v - tau, 0, cap)) = 1 by a vectorised grid search refined four times."""
    lo, hi = v.min() - cap, v.max()
    for _ in range(4):
        taus = np.linspace(lo, hi, 65)
        tot = np.clip(v[None, :] - taus[:, None], 0.0, cap).sum(1)     # decreasing in tau
        j = int(np.searchsorted(-tot, -1.0))                           # first tau with total <= 1
        j = min(max(j, 1), 64)
        lo, hi = taus[j - 1], taus[j]
    return np.clip(v - 0.5 * (lo + hi), 0.0, cap)


def _ew_index(daily):
    """Equal-weight index of the universe from completed closes (rebalanced daily)."""
    r = daily.pct_change().mean(axis=1).fillna(0.0)
    return (1.0 + r).cumprod()


def _risk_state(daily, ma_win=100, mom_win=20, vol_win=20):
    """Regime inputs from completed closes only."""
    key = ("rs", daily.index[-1], len(daily), ma_win, mom_win, vol_win)
    return _cached(key, lambda: _risk_state_raw(daily, ma_win, mom_win, vol_win))


def _risk_state_raw(daily, ma_win, mom_win, vol_win):
    idx = _ew_index(daily)
    r = daily.pct_change().iloc[-63:]
    C = r.corr().to_numpy()
    n = C.shape[0]
    avg_corr = float((np.nansum(C) - n) / (n * (n - 1)))
    return {
        "above_ma": bool(idx.iloc[-1] >= idx.iloc[-ma_win:].mean()),
        "mom": float(idx.iloc[-1] / idx.iloc[-1 - mom_win] - 1.0),
        "vol": float(idx.pct_change().iloc[-vol_win:].std() * np.sqrt(252)),
        "corr": avg_corr,
    }


def _rule_v2(observation, S0=0.25, S1=0.40, theta=BASE_THETA, opening_theta=OPEN_THETA, k=0.5, g=0.05,
             mv_blend=0.5, mv_cap=0.10, shock=True, trend_gate=True, ma_win=100, mom_win=20,
             vol_target=None, corr_cut=None, off_exposure=0.0, miss_rule=True):
    syms = observation["symbols"]
    n = len(syms)
    port = observation["portfolio"]
    started = bool(port.get("positions"))
    if started and observation["round"]["number"] != 1:
        return None

    daily = get_daily_close(observation, lookback=253).reindex(columns=syms)
    w = port.get("weights") or {}
    cur = np.array([float(w.get(s, 0.0)) for s in syms])

    # ---- exposure ----------------------------------------------------------------------------------
    st = _risk_state(daily, ma_win=ma_win, mom_win=mom_win) if len(daily) >= max(ma_win, 64) + 1 else None
    risk_on = True
    if st is not None and trend_gate:
        risk_on = st["above_ma"] and st["mom"] > 0.0
    if st is not None and corr_cut is not None and st["corr"] > corr_cut:
        risk_on = False

    if not risk_on:
        S = off_exposure
        fire = False
    else:
        switched = S1 is not None and shock and started and cur.sum() > (S0 + S1) / 2
        fire = bool(S1 is not None and shock and started and not switched and _shock_yesterday(daily))
        S = S1 if (switched or fire) else S0
        if vol_target is not None and st is not None and st["vol"] > 0:
            S = min(S, S * vol_target / st["vol"])

    # ---- composition: equal weight blended with correlation-aware minimum variance ----------------------
    base = np.full(n, 1.0 / n)
    if mv_blend > 0 and len(daily) >= 127:
        base = (1 - mv_blend) * base + mv_blend * _min_var_weights(daily, cap=mv_cap)
    z = _cached(("sig", daily.index[-1], len(daily)), lambda: _signal_rank_tuned(daily, n))
    th = opening_theta if not started else theta
    target = np.clip(S * base + th * z * (S / 0.25), 0.0, 0.30)   # tilt scaled with exposure
    if target.sum() > 0:
        target = target * (S / target.sum())

    excl = _cached(("ex", daily.index[-1], observation["round"].get("id")), lambda: _excluded(observation, daily, syms)) if miss_rule else np.zeros(n, dtype=bool)
    target[excl] = 0.0

    if not started or fire or S == 0.0 and cur.sum() > 0:
        new = target                       # first purchase / shock / risk-off exit: straight to target
    else:
        must_sell = bool((excl & (cur > 1e-4)).any())
        if np.abs(target - cur).sum() < g * max(S, cur.sum()) / 0.25 and not must_sell:
            return None
        new = cur + k * (target - cur)
        new[excl] = 0.0

    new = np.clip(new, 0.0, 0.30)
    if new.sum() > 1:
        new = new / new.sum()
    out = zero_weights()
    out.update({s: float(v) for s, v in zip(syms, new)})
    return out


def make(**kw):
    def f(observation):
        return _rule_v2(observation, **kw)
    f.name = "BreadthGuard v2 " + " ".join(f"{a}={b}" for a, b in kw.items())
    return f
