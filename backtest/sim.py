"""Local replica of the "Compare my strategies" evaluator.

* 65 consecutive 15-trading-day windows from 2022-02-01 (each starts from cash, $1M).
* Round 1 of each day is at the open: the strategy sees completed daily closes up to the previous
  day and its current weights; a returned dict is filled at the open (cost_bps per unit turnover).
  Other rounds are not simulated (every strategy here holds outside Round 1).
* The portfolio is marked at every intraday point: hourly bars where Yahoo has them (Nov 2023 on),
  otherwise open and close.
* Per window, each strategy gets four metrics - return, stability (mean/std of point returns),
  max drawdown, volatility - each ranked across entrants (ties share the average rank).
  score = mean of the four ranks; place = rank of the score.
"""
import os
import sys
import importlib.util
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from testbed import SYMBOLS  # noqa: E402

DATA = os.path.join(ROOT, "data")


def _load():
    o = pd.read_csv(os.path.join(DATA, "daily_open.csv"), index_col=0, parse_dates=True)[SYMBOLS]
    c = pd.read_csv(os.path.join(DATA, "daily_close.csv"), index_col=0, parse_dates=True)[SYMBOLS]
    h = None
    p = os.path.join(DATA, "hourly_close.csv")
    if os.path.exists(p):
        h = pd.read_csv(p, index_col=0)
        h.index = pd.to_datetime(h.index, utc=True).tz_convert("America/New_York").tz_localize(None)
        h = h[SYMBOLS].ffill()
    return o, c, h


OPEN, CLOSE, HOURLY = _load()
_HOURLY_BY_DAY = {d: g for d, g in HOURLY.groupby(HOURLY.index.normalize())} if HOURLY is not None else {}


def load_module(path, name=None):
    name = name or os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def windows(start="2022-02-01", end="2025-12-31", length=15):
    days = CLOSE.loc[start:end].index
    return [days[i:i + length] for i in range(0, len(days) - length + 1, length)]


def _intraday_marks(day):
    """Price rows (after the open) at which the book is marked during `day`."""
    if HOURLY is not None:
        h = _HOURLY_BY_DAY.get(pd.Timestamp(day).normalize())
        if h is not None and len(h) >= 2 and np.isfinite(h.values).all():
            # adjusted hourly closes are not on the same scale as daily adjusted prices: rescale so the
            # last hourly mark equals the daily close
            rows = h.values / h.values[-1] * CLOSE.loc[day].values
            return rows[:-1].tolist() + [CLOSE.loc[day].values]
    return [CLOSE.loc[day].values]


_MARK_CACHE = {}


def marks(day):
    if day not in _MARK_CACHE:
        _MARK_CACHE[day] = _intraday_marks(day)
    return _MARK_CACHE[day]


# --------------------------------------------------------------------------- benchmarks
def bench_cash(obs):
    return None


def bench_ew(obs):
    if obs["portfolio"]["positions"]:
        return None
    return {s: 1.0 / 30 for s in obs["symbols"]}


def _topk(obs, scores, k=5):
    if obs["round"]["number"] != 1:
        return None
    idx = np.argsort(scores)[-k:]
    out = {s: 0.0 for s in obs["symbols"]}
    for i in idx:
        out[obs["symbols"][i]] = 1.0 / k
    return out


def bench_losers(obs):
    d = obs["_daily"]
    return _topk(obs, -(d.iloc[-1].values / d.iloc[-2].values - 1))


def bench_winners(obs):
    d = obs["_daily"]
    return _topk(obs, d.iloc[-1].values / d.iloc[-21].values - 1)


bench_cash.name = "Cash only"
bench_ew.name = "Equal weight, buy & hold"
bench_losers.name = "Buy yesterday's losers"
bench_winners.name = "Kit example (recent winners)"
BENCHMARKS = [bench_cash, bench_ew, bench_losers, bench_winners]


# --------------------------------------------------------------------------- simulation
LAST_TURNOVER = [0.0]


def run_window(fn, days, cost_bps=2.0, reset=None, capital=1_000_000.0, min_fee=0.0, whole_shares=False):
    """Returns the array of portfolio values (start, then every mark) for one window.
    The window's total traded notional / value is left in LAST_TURNOVER[0]."""
    traded = 0.0
    if reset:
        reset()
    cash, shares = capital, np.zeros(30)
    vals = [capital]
    for day in days:
        pos = CLOSE.index.get_loc(day)
        daily = CLOSE.iloc[max(0, pos - 420):pos]
        px = OPEN.loc[day].values
        value = cash + shares @ px
        w = shares * px / value
        obs = {
            "symbols": list(SYMBOLS),
            "portfolio": {"positions": {s: float(q) for s, q in zip(SYMBOLS, shares) if q > 0},
                          "weights": {s: float(x) for s, x in zip(SYMBOLS, w)}, "cash": cash, "value": value},
            "round": {"number": 1, "id": f"validation-{day.date()}-r1"},
            "as_of": pd.Timestamp(day) + pd.Timedelta(hours=9, minutes=30),
            "daily_close": daily,
            "window_start": str(days[0].date()),
            "_daily": daily,
        }
        tgt = fn(obs)
        if tgt is not None:
            t = np.array([max(0.0, float(tgt.get(s, 0.0))) for s in SYMBOLS])
            if t.sum() > 1:
                t = t / t.sum()
            new_sh = t * value / px
            if whole_shares:
                new_sh = np.floor(new_sh + 1e-9)
            order = np.abs(new_sh - shares) * px
            turnover = order.sum()
            cost = (np.maximum(order * cost_bps / 1e4, min_fee) * (order > 1e-9)).sum()
            traded += turnover / value
            cash = cash + (shares - new_sh) @ px - cost
            shares = new_sh
        vals.append(cash + shares @ px)
        for row in marks(day):
            vals.append(cash + shares @ row)
    LAST_TURNOVER[0] = traded
    return np.array(vals)


def metrics(v):
    r = np.diff(v) / v[:-1]
    ret = v[-1] / v[0] - 1
    sd = r.std()
    stab = r.mean() / sd if sd > 1e-12 else 0.0
    dd = float((1 - v / np.maximum.accumulate(v)).max())
    return {"return": ret, "stability": stab, "maxdd": dd, "vol": sd, "worst": float(max(0.0, -r.min())),
            "trading": LAST_TURNOVER[0] / 105.0}


def _rank(x, higher_better):
    s = pd.Series(x)
    # round so numerically-identical results (cash vs. ~cash) tie
    s = s.round(12)
    return s.rank(ascending=not higher_better, method="average").values


def score_table(mets, weights=(1, 1, 1, 1)):
    """mets: list (entrants) of metric dicts for one window -> per-entrant score."""
    R = np.vstack([
        _rank([m["return"] for m in mets], True),
        _rank([m["stability"] for m in mets], True),
        _rank([m["maxdd"] for m in mets], False),
        _rank([m["vol"] for m in mets], False),
    ])
    w = np.asarray(weights, float)[:, None]
    return (R * w).sum(0) / w.sum()


def evaluate(entrants, wins=None, cost_bps=2.0, weights=(1, 1, 1, 1), verbose=False):
    """entrants: list of (label, fn, reset_or_None). Returns (summary DataFrame, per-window metrics)."""
    wins = wins or windows()
    per = {lab: [] for lab, _, _ in entrants}
    for i, days in enumerate(wins):
        for lab, fn, rs in entrants:
            per[lab].append(metrics(run_window(fn, days, cost_bps, rs)))
        if verbose:
            print(f"window {i + 1}/{len(wins)} {days[0].date()}", flush=True)
    return per


def rank_summary(per, labels, weights=(1, 1, 1, 1)):
    nwin = len(per[labels[0]])
    sc = np.zeros((nwin, len(labels)))
    for i in range(nwin):
        sc[i] = score_table([per[l][i] for l in labels], weights)
    place = np.vstack([pd.Series(r).rank(method="min").values for r in sc])
    df = pd.DataFrame({
        "avg_score": sc.mean(0), "avg_place": place.mean(0), "firsts": (place == 1).sum(0),
        "avg_ret%": [100 * np.mean([m["return"] for m in per[l]]) for l in labels],
        "win_vs_cash": [np.mean([m["return"] > 0 for m in per[l]]) for l in labels],
        "avg_dd%": [100 * np.mean([m["maxdd"] for m in per[l]]) for l in labels],
    }, index=labels)
    return df.sort_values("avg_score")


def full_period(fn, reset=None, start="2022-02-01", end="2025-12-31", cost_bps=2.0):
    days = CLOSE.loc[start:end].index
    v = run_window(fn, days, cost_bps, reset)
    m = metrics(v)
    return m, v
