"""Combined_V3 - Combined_V1's Sharpe engine run as a real, risk-managed portfolio (ICAIF 2026 Trading Agent Competition)

What changed versus Combined_V1, and why (see docs/rules.md and docs/evaluation.md in the official kit):
  * Exposure: 20% of NAV (32% after a breadth-confirmed shock) instead of 0.001%. Cumulative return is ranked
    HIGHER = better; V1 gave that rank away to win drawdown/turnover. Sharpe is scale-invariant, so the
    inverse-vol + residual-momentum engine keeps the stability edge V1 showed. E_BASE / E_SHOCK are the knobs.
  * Runs every round (the competition is hourly allocation): Round 1 refreshes the daily signal and rebalances
    only outside a no-trade band; Rounds 2-7 watch the portfolio and can de-risk intraday.
  * Drawdown brake: halve the sleeve at -1.5% from the window's NAV peak, go to cash at -3% (caps max drawdown,
    the metric V1 controlled only by being tiny).
  * Kept from V1: inverse-vol weights tilted by residual momentum (jimin_test_v5), breadth-confirmed -2% shock
    step-up and the earnings-miss exclusion (BreadthGuard), buy-and-hold between signals (low turnover).
  * Kit path re-submits the live portfolio weights on hold rounds (no drift trading); round number is parsed
    from the round id when the API has no `number` field.
Data: daily closes from the testbed, or observation["daily_close"], or Yahoo Finance (public; disclosed).
"""
import json
import os

import numpy as np
import pandas as pd

UNIVERSE = ["AAPL", "MSFT", "NVDA", "INTC", "CRM", "JPM", "BAC", "GS", "V", "PYPL", "LLY", "JNJ", "UNH", "PFE", "TMO",
            "AMZN", "TSLA", "WMT", "NKE", "KO", "CAT", "GE", "BA", "XOM", "CVX", "GOOGL", "META", "DIS", "T", "NEE"]

try:                                                      # team testbed / web tool
    from testbed import get_daily_close, zero_weights
except ImportError:                                       # official kit: bring our own (public) daily closes
    _YF_CACHE = {}

    def _round_day(observation):
        rnd = observation.get("round") or {}
        for v in (rnd.get("day"), str(rnd.get("id", "")).split("-r")[0].split("-", 1)[-1], observation.get("as_of")):
            try:
                return pd.Timestamp(str(v)[:10])
            except (ValueError, TypeError):
                continue
        return pd.Timestamp.now(tz="America/New_York").tz_localize(None).normalize()

    def get_daily_close(observation, lookback=253):
        day = _round_day(observation)
        d = observation.get("daily_close")
        if not isinstance(d, pd.DataFrame):
            if day not in _YF_CACHE:
                import yfinance as yf
                start = (day - pd.Timedelta(days=int(lookback * 1.6) + 30)).strftime("%Y-%m-%d")
                px = yf.download(UNIVERSE, start=start, end=day.strftime("%Y-%m-%d"), auto_adjust=True,
                                 progress=False)["Close"]
                px.index = pd.DatetimeIndex(px.index).tz_localize(None) if px.index.tz else pd.DatetimeIndex(px.index)
                _YF_CACHE[day] = px
            d = _YF_CACHE[day]
        d = d[pd.DatetimeIndex(d.index).normalize() < day]   # completed closes only
        return d.reindex(columns=UNIVERSE).iloc[-lookback:]

    def zero_weights():
        return {s: 0.0 for s in UNIVERSE}

NAME = "Combined_V3"

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



# ----------------------------------------------------------------------------------- residual momentum (jimin_test_v5)
BETA_WIN = 120
LOOKBACK = 400            # resmom needs 252 + 120 + 1 completed closes; with less it falls back to 12-1 momentum

SECTOR = {'GOOGL': 'Comm', 'META': 'Comm', 'NEE': 'Comm', 'T': 'Comm', 'DIS': 'Comm',
          'WMT': 'Cons', 'KO': 'Cons', 'TSLA': 'Cons', 'AMZN': 'Cons', 'NKE': 'Cons',
          'BAC': 'Fin', 'GS': 'Fin', 'PYPL': 'Fin', 'JPM': 'Fin', 'V': 'Fin',
          'UNH': 'Hlth', 'JNJ': 'Hlth', 'LLY': 'Hlth', 'PFE': 'Hlth', 'TMO': 'Hlth',
          'XOM': 'Ind', 'GE': 'Ind', 'CVX': 'Ind', 'CAT': 'Ind', 'BA': 'Ind',
          'MSFT': 'Tech', 'INTC': 'Tech', 'CRM': 'Tech', 'NVDA': 'Tech', 'AAPL': 'Tech'}


def residual_momentum(daily, L=BETA_WIN):
    """daily: DataFrame of closes (rows = days, oldest first). Returns raw residual-momentum score per column (NaN if short)."""
    X = daily.values.astype(float)
    n = X.shape[1]
    if len(X) < 252 + L + 1:
        return None
    R = np.log(X[1:] / X[:-1])                       # R[j] = return into day j+1
    R = np.where(np.isfinite(R), R, np.nan)
    ok = np.isfinite(R)
    Rz = np.where(ok, R, 0.0)
    mkt = Rz.sum(1) / np.maximum(ok.sum(1), 1)
    sec = np.array([SECTOR.get(c, c) for c in daily.columns])
    M = (sec[:, None] == sec[None, :]).astype(float)
    cnt = ok.astype(float) @ M
    sec_ex = np.where(cnt - ok > 0, (Rz @ M - Rz) / np.maximum(cnt - ok, 1), mkt[:, None])
    T = len(R)
    x1 = np.repeat(mkt[:, None], n, 1); x2 = sec_ex

    def ws(Z):                                        # sum over [t-L, t) for each t
        cs = np.cumsum(np.vstack([np.zeros((1, n)), Z]), 0)
        out = np.full((T, n), np.nan)
        out[L:] = cs[L:T] - cs[:T - L]
        return out
    S11, S12, S22, S1y, S2y = ws(x1 * x1), ws(x1 * x2), ws(x2 * x2), ws(x1 * Rz), ws(x2 * Rz)
    det = S11 * S22 - S12 ** 2
    with np.errstate(all="ignore"):
        b1 = (S22 * S1y - S12 * S2y) / det
        b2 = (S11 * S2y - S12 * S1y) / det
    E = R - b1 * x1 - b2 * x2
    # last row of R = return into the last completed day (t-1). formation days t-252 .. t-22  -> R rows [-252, -21)
    e = E[-252:-21]
    with np.errstate(all="ignore"):
        s = np.nansum(e, 0) / (np.nanstd(e, 0) + 1e-12)
    s[np.isnan(e).any(0)] = np.nan
    return s



def _signal(daily, n):
    s = residual_momentum(daily)
    if s is None:
        if len(daily) < 253:
            return np.zeros(n)
        return _zscore(daily.iloc[-22].values / daily.iloc[-253].values - 1)
    return _zscore(s)


# ----------------------------------------------------------------------------------- breadth-confirmed shock (BreadthGuard)
SHOCK_DROP = -0.02

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



# ----------------------------------------------------------------------------------- the rule (V3)
# Exposure is the one knob that trades the return rank against the drawdown/turnover ranks.  Sharpe does not
# depend on it, so the inv-vol + resmom engine keeps its stability edge at any size.  Sweep these in field2.py.
E_BASE = 0.20             # stock sleeve as a fraction of NAV in normal conditions
E_SHOCK = 0.32            # sleeve after a breadth-confirmed -2% selloff (same 1.6x step as BreadthGuard 25->40)
TILT = 0.6                # residual-momentum tilt: w_i ~ (1/vol_i) * (1 + TILT * z_i)
VOL_WIN = 60              # days for the inverse-volatility weights
BAND = 0.25               # Round-1 rebalance only if sum|target - current| > BAND * sleeve (no-trade band)
DD_HALF = 0.015           # NAV drawdown from the window's peak that halves the sleeve
DD_OUT = 0.030            # NAV drawdown that moves to cash for the rest of the window
PER_NAME_CAP = 0.30
INITIAL_NAV = 1_000_000.0


def _round_number(observation):
    rnd = observation.get("round") or {}
    n = rnd.get("number") if isinstance(rnd, dict) else None
    if n is None:
        try:
            n = int(str(rnd.get("id", "")).rsplit("-r", 1)[1])
        except (IndexError, ValueError, AttributeError):
            n = 1
    return int(n)


def _nav(port):
    for k in ("nav", "total_value", "value", "equity", "portfolio_value"):
        v = port.get(k) if isinstance(port, dict) else None
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return None


def _base_weights(daily, z):
    r = daily.pct_change().iloc[-VOL_WIN:]
    vol = r.std().to_numpy(dtype=float)
    ok = np.isfinite(vol) & (vol > 0)
    iv = np.where(ok, 1.0 / np.where(ok, vol, 1.0), 0.0)
    b = np.clip(iv * (1.0 + TILT * z), 0.0, None)
    return b / b.sum() if b.sum() > 0 else np.full(len(z), 1.0 / len(z))


class _Window:
    """Per-phase/window memory: regime (base/shock), NAV peak, drawdown state."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.last_day = None
        self.shocked = False
        self.peak = None
        self.level = 1.0          # 1.0 normal, 0.5 after DD_HALF, 0.0 after DD_OUT (sticky for the window)


def _decide(observation, cur, started, mem, nav=None, e_base=E_BASE, e_shock=E_SHOCK):
    """Core decision, called EVERY round. Returns (weights array or None for hold).

    Round 1: refresh the daily signal; trade if the shock fires, an earnings miss excludes a held name, or the
    holding has drifted outside the no-trade band.  Rounds 2-7: only the drawdown brake can trade intraday.
    """
    syms = observation["symbols"]
    n = len(syms)
    rnd = _round_number(observation)
    # ---- drawdown brake (any round) -------------------------------------------------------------------------
    brake = False
    if nav is not None:
        mem.peak = nav if mem.peak is None else max(mem.peak, nav)
        dd = 1.0 - nav / mem.peak if mem.peak > 0 else 0.0
        new_level = 0.0 if dd >= DD_OUT else (0.5 if dd >= DD_HALF else 1.0)
        if new_level < mem.level:
            mem.level, brake = new_level, True
    if brake:
        if mem.level == 0.0:
            return np.zeros(n)
        return np.clip(cur * 0.5, 0.0, PER_NAME_CAP)                   # halve the current holding

    if started and rnd != 1:
        return None                                        # intraday: hold unless the brake fired
    if mem.level == 0.0:
        return None if cur.sum() == 0 else np.zeros(n)

    daily = get_daily_close(observation, lookback=LOOKBACK).reindex(columns=syms)
    fire = started and not mem.shocked and _shock_yesterday(daily)
    if fire:
        mem.shocked = True
    S = (e_shock if mem.shocked else e_base) * mem.level

    target = S * _base_weights(daily, _signal(daily, n))
    excl = _excluded(observation, daily, syms)
    target[excl] = 0.0                                     # earnings miss -> cash for 15 trading days
    target = np.clip(target, 0.0, PER_NAME_CAP)

    if not started or fire:
        return target
    if (excl & (cur > 0)).any():
        new = cur.copy()
        new[excl] = 0.0
        return new
    if np.abs(target - cur).sum() > BAND * S:
        return target                                      # drift / signal change outside the band
    return None


def _out(syms, w):
    out = zero_weights()
    out.update({s: float(v) for s, v in zip(syms, w)})
    return out


def make_rule(e_base=E_BASE, e_shock=E_SHOCK, name=None):
    """Factory for testbed sweeps: make_rule(0.10, 0.16), make_rule(0.30, 0.48), ..."""
    mem = _Window()

    def rule(observation):
        syms = observation["symbols"]
        port = observation["portfolio"]
        w = port.get("weights") or {}
        cur = np.array([float(w.get(s, 0.0)) for s in syms])
        started = bool(port.get("positions"))
        nav = _nav(port)
        day = str((observation.get("round") or {}).get("id", "")) or str(observation.get("as_of", ""))
        fresh = not started and cur.sum() == 0 and (nav is None or abs(nav - INITIAL_NAV) < 1e-6)
        if fresh or (mem.last_day is not None and day and day < mem.last_day):
            mem.reset()                                    # new test window -> forget regime / peak / brake
        mem.last_day = day or mem.last_day
        new = _decide(observation, cur, started, mem, nav, e_base, e_shock)
        return None if new is None else _out(syms, new)

    rule.name = name or f"Combined_V3 ({e_base:.0%}->{e_shock:.0%})"
    return rule


combined_v3 = make_rule()


# ----------------------------------------------------------------------------------- official kit
STATE_FILE = os.environ.get("COMBINED_V3_STATE", ".icaif/combined_v3_state.json")


def _load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_state(phase, d):
    st = _load_state()
    st[phase] = d
    os.makedirs(os.path.dirname(STATE_FILE) or ".", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(st, f, indent=1)


def kit_strategy(observation):
    """For `tools/auto_submit.py watch` (needs 30 weights every round).

    On hold rounds it re-submits the CURRENT weights from the live portfolio when the API provides them, so a hold
    trades ~nothing; it falls back to the last target only if the portfolio has no weights field."""
    syms = list(observation["symbols"])
    phase = observation["phase"]
    st = _load_state().get(phase) or {}
    port = observation.get("portfolio") or {}
    live_w = port.get("weights") or {}
    prev = st.get("target") or {}
    cur_src = live_w if live_w else prev
    cur = np.array([float(cur_src.get(s, 0.0)) for s in syms])

    mem = _Window()
    mem.shocked, mem.peak, mem.level = st.get("shocked", False), st.get("peak"), st.get("level", 1.0)
    new = _decide(observation, cur, cur.sum() > 0 or bool(prev), mem, _nav(port))
    w = _out(syms, new) if new is not None else _out(syms, cur)
    _save_state(phase, {"target": w if new is not None else (prev or w), "shocked": mem.shocked,
                        "peak": mem.peak, "level": mem.level, "round_id": (observation.get("round") or {}).get("id")})
    return w


def strategy(observation):
    """Default entry point (team testbed). None = hold."""
    return combined_v3(observation)


strategy.name = "Combined_V3"
