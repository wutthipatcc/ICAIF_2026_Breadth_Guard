"""Combined_V5 without Tesla: TSLA is never held (always submitted at 0).
Result (backtest/results_v5_variants.md): 65 windows 4.59 (#1 of real portfolios; V5 4.49), Oct windows 4.25 (= V5),
2022-25 one run +6.9%, max drawdown 2.3%.
Everything else is identical to Combined_V5 (description below).

Combined_V5 - a real, risk-managed portfolio built from PairTrading V5.1, BreadthGuard v2 and jimin_test_v5
(ACM ICAIF 2026 Trading Agent Competition)

Objective (official kit docs/evaluation.md): teams are ranked on cumulative return (higher), Sharpe of per-round
returns (higher), maximum drawdown (lower) and turnover (lower); the score is the mean of the four ranks.

What changed from Combined_V4, and why (Combined_V4_Review_and_V5_Proposal + the Q18-Q23 composite-rank charts):
  * V4 held $5 of $1M. It follows the rules but does not manage a portfolio, which is hard to defend in the code /
    video review, and past competitions show a whole column of cash and near-cash teams at 0% return. V5 holds a
    real sleeve: median 11% of NAV, 5-15% in normal markets, up to ~40% after a broad selloff.
  * The charts: return (R^2 0.36-0.61) and Sharpe (0.34-0.57) predict composite rank best; low turnover helps
    (top teams < 4% average turnover); drawdown matters least. So V5 keeps a high-Sharpe book, trades rarely and
    never locks in a loss.

The rule
  Sizing   sleeve = SIGMA_TARGET / forecast volatility of the book (60-day), halved when the equal-weight index is
           below its 100-day mean and down over 20 days; set once at the first purchase (SIZE_LOCK) so the book is
           not traded on every wiggle of the volatility estimate.                        [review A, tested]
  Shape    weights ~ vol^-0.5 x (1 + 0.6 z), z = residual momentum (market + sector betas, 12-1 window). [V4/jimin]
  Shock    x2.4 after a breadth-confirmed -2% selloff (>= 65% of names down, median <= -0.5%).  [BreadthGuard v2]
  Misses   EPS surprise < -0.5% -> that name in cash for 15 trading days; refresh_misses() before every Round 1.
  Drawdown graduated, not sticky: sleeve x max(0.3, 1 - DD/5%); checked every round (R2-R7 can de-risk in steps of
           0.2), and Round 1 re-sizes up again as NAV recovers.                        [review B; fixes V3's lock-in]
  Trading  Round 1 re-targets only outside a 30%-of-sleeve no-trade band; R2-R7 trade only for the drawdown control;
           otherwise hold = no upload (no trade, no fee).                                   [review C]
  Earnings an overlay that steps out of a name the session before its report is built in (refresh_earnings,
           EARN_CUT) but OFF: at 0.5 and 1.0 it lowered the score in every test set (lost the post-report drift and
           paid fees).                                                                 [review D, tested, not adopted]

Tested in a field that looks like past competitions (backtest/field5.py: cash and near-cash teams, 30-100% equal-weight
books, momentum, mean reversion, vol targeting, an every-round rebalancer, kit benchmarks and our own agents;
10 bp fees; Rounds 2-7 simulated from 2023-10). See backtest/results_combined_v5.md:
  * 65 rolling windows: 1st of the teams that hold a real portfolio (4.49 vs BreadthGuard v2 4.95); best drawdown
    and turnover ranks among them.
  * Oct 12-30 earnings-season windows 2022-25 (the Official slot, only 4 windows): 1st, 4.25 vs BreadthGuard v2 4.81.
  * Whole field: 5th of 20, behind V4, PairTrading, Cash and a near-cash clone - the rank score still rewards holding
    almost nothing; V5 is the best agent that actually invests.
  * One run 2022-02 .. 2025-12: +6.5%, max drawdown 2.3%.
SIGMA_TARGET is the size knob: 0.02 / 0.025 give more return and rank lower (lab5 v5d).

Fixes carried over from the review (F): round number from the '-rN' id or the ET clock (never silently 1); hold
rounds upload nothing (run_combined_v5.py) or re-submit LIVE weights (kit_strategy); misses refreshed before every
Round 1; NAV, weights and positions read from the portfolio API, the state file only keeps the window memory.

Data: observation["daily_close"] or Yahoo Finance daily closes completed before the decision day; Yahoo quoteSummary
earnings data (public; permitted by docs/llm_and_external_data.md - disclose it). No LLM.
Entry points: strategy(observation) (testbed, None = hold); kit_decide / kit_strategy (official kit);
make_rule(**overrides) for research sweeps.
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

NAME = "Combined_V5_noTSLA"

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
    """Breadth-confirmed shock (BreadthGuard v2): yesterday's equal-weight return <= -2%, >= 65% of names down and
    the median name down >= 0.5%, so one or two idiosyncratic crashes do not count as a market-wide selloff."""
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




# ----------------------------------------------------------------------------------- earnings calendar (overlay)
# EARNINGS[sym] = set of "gap days": the first trading day whose OPEN reflects a report (report before 09:30 ET ->
# that day, otherwise the next day).  Filled live by refresh_earnings() (Yahoo quoteSummary, public) or, for
# backtests, by load_earnings_csv("data/earnings_days.csv").
EARNINGS = {}


def _gap_day(ts):
    ts = pd.Timestamp(ts)
    d = ts.normalize()
    if ts.hour * 60 + ts.minute >= 9 * 60 + 30:
        d = d + pd.offsets.BDay(1)
    return d


def load_earnings_csv(path):
    df = pd.read_csv(path, parse_dates=["gap_day"])
    for t, g in df.groupby("symbol"):
        EARNINGS.setdefault(t, set()).update(pd.DatetimeIndex(g.gap_day).normalize())
    return len(df)


def refresh_earnings(symbols=UNIVERSE):
    """Next scheduled report of every name from Yahoo's quoteSummary API (public). Returns the number added."""
    from yfinance.data import YfData
    yd, added = YfData(), 0
    for t in symbols:
        try:
            r = yd.get_raw_json(f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{t}",
                                params={"modules": "calendarEvents"})["quoteSummary"]["result"][0]
            for x in r["calendarEvents"]["earnings"].get("earningsDate", []):
                ts = pd.Timestamp(x["raw"], unit="s", tz="UTC").tz_convert("America/New_York").tz_localize(None)
                g = _gap_day(ts)
                if g not in EARNINGS.setdefault(t, set()):
                    EARNINGS[t].add(g)
                    added += 1
        except Exception:
            continue
    return added


def _reports_next(today, syms):
    """Names whose report hits the NEXT session's open (gap day = next business day after `today`)."""
    nxt = pd.Timestamp(today).normalize() + pd.offsets.BDay(1)
    return np.array([nxt in EARNINGS.get(s, ()) for s in syms])


# ----------------------------------------------------------------------------------- the rule (V5)
# Sizing: the stock sleeve is set so the BOOK's forecast volatility hits SIGMA_TARGET (annualised), then scaled by the
# trend regime and the window drawdown, and capped.  Shape (sqrt-inv-vol x residual momentum) is V4's.
SIGMA_TARGET = 0.015      # annualised volatility target for the WHOLE portfolio -> ~8-10% sleeve in normal markets
S_MIN, S_MAX = 0.05, 0.60 # sleeve bounds
TREND_CUT = 0.5           # sleeve multiplier when the equal-weight index is below its 100-day mean and 20-day return < 0
SHOCK_STEP = 2.4          # sleeve x 2.4 after a breadth-confirmed -2% selloff (BreadthGuard v2: 15% -> 36%)
DD_MAX = 0.05             # graduated drawdown control: sleeve x max(DD_FLOOR, 1 - DD / DD_MAX) (safety net)
DD_FLOOR = 0.3
DD_STEP = 0.2             # intraday, act only when the drawdown scale falls by >= one step (no churn)
EARN_CUT = 0.0            # fraction of a name's weight removed the session before its report. OFF: tested 0.5 / 1.0,
                          # both lowered the score (lost the post-report drift and paid fees) - see lab5 v5e
TILT = 0.6                # residual-momentum tilt: w_i ~ vol_i ** -IV_POW * (1 + TILT * z_i)
IV_POW = 0.5
VOL_WIN = 60
SIZE_LOCK = True          # size the sleeve once (first purchase); afterwards only shock / drawdown change it
BAND = 0.30               # Round-1 no-trade band: trade only if sum|target - held| > BAND x sleeve
PER_NAME_CAP = 0.30
EXCLUDE = ("TSLA",)  # symbols never held (always submitted at 0); signals still use them as peers
INITIAL_NAV = 1_000_000.0


def _round_number(observation):
    """Round 1-7 from round.number, else the '-rN' id suffix, else the ET clock (never silently 1)."""
    rnd = observation.get("round") or {}
    n = rnd.get("number") if isinstance(rnd, dict) else None
    if n is None:
        try:
            n = int(str(rnd.get("id", "")).rsplit("-r", 1)[1])
        except (IndexError, ValueError, AttributeError):
            n = None
    if n is None:
        try:
            t = pd.Timestamp(observation.get("as_of"))
            t = t.tz_convert("America/New_York") if t.tzinfo else t
            n = 1 if (t.hour, t.minute) < (9, 30) or t.hour >= 16 else min(7, max(1, t.hour - 8))
        except (TypeError, ValueError):
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


def _shape(daily, z):
    r = daily.pct_change().iloc[-VOL_WIN:]
    vol = r.std().to_numpy(dtype=float)
    ok = np.isfinite(vol) & (vol > 0)
    iv = np.where(ok, np.where(ok, vol, 1.0) ** -IV_POW, 0.0)
    b = np.clip(iv * (1.0 + TILT * z), 0.0, None)
    keep = ~np.isin(np.asarray(daily.columns), list(EXCLUDE))
    b = np.where(keep, b, 0.0)
    return b / b.sum() if b.sum() > 0 else keep / keep.sum()


def _book_vol(daily, b):
    r = daily.pct_change().iloc[-VOL_WIN:].fillna(0.0).to_numpy(dtype=float)
    return float(np.std(r @ b) * np.sqrt(252))


def _trend_down(daily):
    ew = daily.pct_change().iloc[-100:].mean(axis=1).fillna(0.0)
    idx = (1 + ew).cumprod()
    return bool(idx.iloc[-1] < idx.mean() and idx.iloc[-1] < idx.iloc[-21])


class _Window:
    """Per-phase memory: NAV peak, drawdown scale, shock regime."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.peak = None
        self.dd_scale = 1.0
        self.shocked = False
        self.base = None          # sleeve chosen at the first purchase (SIZE_LOCK)
        self.last_key = None


def _dd_scale(mem, nav):
    if nav is None:
        return mem.dd_scale
    mem.peak = nav if mem.peak is None else max(mem.peak, nav)
    dd = 1.0 - nav / mem.peak if mem.peak > 0 else 0.0
    return max(DD_FLOOR, 1.0 - dd / DD_MAX)


def _decide(observation, cur, started, mem, nav=None):
    """Called EVERY round. Returns the new target weights (array) or None to hold.

    Round 1: refresh the daily signal and sizing; trade on the first purchase, a shock step-up, an earnings-miss
    exclusion, a scheduled report tomorrow, or when the book is outside the no-trade band.
    Rounds 2-7: only the graduated drawdown control can trade (scale the held book down)."""
    syms = list(observation["symbols"])
    n = len(syms)
    rnd = _round_number(observation)
    scale = _dd_scale(mem, nav)
    if started and rnd != 1:
        if scale <= mem.dd_scale - DD_STEP + 1e-12:          # drawdown deepened by >= one step: de-risk now
            new = cur * (scale / mem.dd_scale)
            mem.dd_scale = scale
            return np.clip(new, 0.0, PER_NAME_CAP)
        return None

    daily = get_daily_close(observation, lookback=LOOKBACK).reindex(columns=syms)
    if started and not mem.shocked and _shock_yesterday(daily):
        mem.shocked = True
        fire = True
    else:
        fire = False
    b = _shape(daily, _signal(daily, n))
    if SIZE_LOCK and mem.base is not None and started:
        S = mem.base
    else:
        S = SIGMA_TARGET / max(_book_vol(daily, b), 1e-6)
        if _trend_down(daily):
            S *= TREND_CUT
        S = float(np.clip(S, S_MIN, S_MAX))
        mem.base = S
    if mem.shocked:
        S *= SHOCK_STEP
    S = float(np.clip(S, S_MIN, S_MAX)) * scale               # Round 1 re-sizes with the current drawdown scale
    mem.dd_scale = scale                                     # (recovers as NAV recovers - no lock-in)

    target = np.minimum(S * b, PER_NAME_CAP)
    excl = _excluded(observation, daily, syms)
    target[excl] = 0.0                                       # earnings miss -> cash for 15 trading days
    rep = (_reports_next(_decision_day(observation, daily), syms) & ~excl) if EARN_CUT > 0 else np.zeros(n, bool)
    target[rep] *= (1.0 - EARN_CUT)                          # report before the next open -> step aside

    if not started or fire:
        return target
    if (excl & (cur > 1e-12)).any() or (rep & (cur > target + 1e-12)).any():
        return target                                        # forced: miss exclusion / tomorrow's report
    if np.abs(target - cur).sum() > BAND * max(S, 1e-9):
        return target                                        # drift, re-entry after a report, sizing change
    return None


def _out(syms, w):
    out = zero_weights()
    out.update({s: float(v) for s, v in zip(syms, w)})
    return out


def make_rule(name=None, **params):
    """Testbed / research entry point. Keyword params override the module constants for this rule only."""
    mem = _Window()
    g = globals()

    def rule(observation):
        saved = {k: g[k] for k in params}
        g.update(params)
        try:
            syms = observation["symbols"]
            port = observation["portfolio"]
            w = port.get("weights") or {}
            cur = np.array([float(w.get(s, 0.0)) for s in syms])
            started = bool(port.get("positions"))
            nav = _nav(port)
            key = str((observation.get("round") or {}).get("id", "")) or str(observation.get("as_of", ""))
            fresh = not started and cur.sum() == 0 and (nav is None or abs(nav - INITIAL_NAV) < 1e-6)
            if fresh or (mem.last_key is not None and key and key < mem.last_key):
                mem.reset()                                  # new window / phase
            mem.last_key = key or mem.last_key
            new = _decide(observation, cur, started, mem, nav)
            return None if new is None else _out(syms, new)
        finally:
            g.update(saved)

    rule.name = name or "Combined_V5_noTSLA"
    return rule


combined_v5 = make_rule()


def strategy(observation):
    """Default entry point (team testbed / web tool). None = hold."""
    return combined_v5(observation)


strategy.name = "Combined_V5_noTSLA"


# ----------------------------------------------------------------------------------- official kit
STATE_FILE = os.environ.get("COMBINED_V5_NOTSLA_STATE", ".icaif/combined_v5_notsla_state.json")


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


def refresh_misses(today=None):
    """Add earnings misses published since MISS_TABLE was written (Yahoo quoteSummary earningsChart; public).
    A report before 09:30 ET is effective that day, otherwise the next business day. Returns the number added."""
    from yfinance.data import YfData
    today = pd.Timestamp(today or pd.Timestamp.now(tz="America/New_York").tz_localize(None)).normalize()
    yd, added = YfData(), 0
    for t in UNIVERSE:
        try:
            r = yd.get_raw_json(f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{t}",
                                params={"modules": "earnings"})["quoteSummary"]["result"][0]
            quarters = r["earnings"]["earningsChart"]["quarterly"]
        except Exception:
            continue
        known = {d for d, _ in _MISS.get(t, [])}
        for q in quarters:
            try:
                srp = float(q["surprisePct"])
                ts = pd.Timestamp(q["reportedDate"]["raw"], unit="s", tz="UTC").tz_convert("America/New_York")
            except (KeyError, TypeError, ValueError):
                continue
            eff = _gap_day(ts.tz_localize(None))
            if srp < MISS_THR and eff <= today and eff not in known:
                add_miss(t, eff.strftime("%Y%m%d"), srp)
                added += 1
    return added


def kit_decide(observation):
    """Official-kit path. Returns the 30 weights to upload, or None when the agent holds (upload nothing: a missing
    decision holds the portfolio with no trade and no fee - docs/rules.md).

    Uses the live portfolio (weights, positions, NAV) from the API when present; the state file keeps the window
    memory (NAV peak, drawdown scale, shock) and the last uploaded target as a fallback for the weights."""
    syms = list(observation["symbols"])
    phase = observation["phase"]
    st = _load_state().get(phase) or {}
    port = observation.get("portfolio") or {}
    live = port.get("weights") or {}
    prev = st.get("target") or {}
    src = live if live else prev
    cur = np.array([float(src.get(s, 0.0)) for s in syms])
    mem = _Window()
    mem.peak, mem.dd_scale, mem.shocked = st.get("peak"), st.get("dd_scale", 1.0), st.get("shocked", False)
    mem.base = st.get("base")
    started = bool(port.get("positions")) or cur.sum() > 0
    new = _decide(observation, cur, started, mem, _nav(port))
    w = None if new is None else _out(syms, new)
    _save_state(phase, {"target": w or prev, "peak": mem.peak, "dd_scale": mem.dd_scale, "shocked": mem.shocked,
                        "base": mem.base, "round_id": (observation.get("round") or {}).get("id")})
    return w


def kit_strategy(observation):
    """For `tools/auto_submit.py watch`, which needs weights every round. On hold rounds it re-submits the LIVE
    portfolio weights (no trade); only if the API gives none does it fall back to the last uploaded target."""
    w = kit_decide(observation)
    if w is not None:
        return w
    live = (observation.get("portfolio") or {}).get("weights") or {}
    if live:
        return _out(observation["symbols"], [float(live.get(s, 0.0)) for s in observation["symbols"]])
    prev = (_load_state().get(observation["phase"]) or {}).get("target")
    return prev if prev else _out(observation["symbols"], np.zeros(len(observation["symbols"])))
