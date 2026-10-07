"""Realistic competition field for Combined_V5 (review doc, step G) + an every-round simulator.

* run_window_rounds: Round 1 at the open as in sim.run_window, plus Rounds 2-7 at the hourly marks where Yahoo has
  hourly bars (2023-10 on); before that only Round 1 is simulated.  10 bp fees, fractional shares.
* Field: the kind of teams seen in past competitions (composite-rank charts Q18-Q23): cash and near-cash teams (the
  column at 0% return), 30/60/100% equal-weight books, momentum, mean reversion, volatility targeting, an every-round
  rebalancer, plus our own agents (PairTrading, BreadthGuard v2, jimin v5, Combined_V3, Combined_V4) and the kit
  benchmarks.  Score = mean of the ranks of return, Sharpe (stability), max drawdown and turnover.
* Windows: the 65 rolling 15-day windows and the 4 "earnings season" windows starting on the first trading day on or
  after Oct 12 (2022-2025), the same calendar slot as the Official phase (Oct 12-30, 2026).
"""
import warnings; warnings.filterwarnings("ignore")
import os, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep, field2, field4, lab3

SY = sim.SYMBOLS
ST = os.path.join(sim.ROOT, "strategies")
COST = 10.0
WINS = sweep.W
OCT = [sim.CLOSE.index[sim.CLOSE.index.searchsorted(pd.Timestamp(f"{y}-10-12"))]
       for y in (2022, 2023, 2024, 2025)]
OCT_WINS = [sim.CLOSE.index[sim.CLOSE.index.get_loc(d):sim.CLOSE.index.get_loc(d) + 15] for d in OCT]


def run_window_rounds(fn, days, cost_bps=COST, reset=None, capital=1_000_000.0, intraday=True):
    traded = 0.0
    if reset:
        reset()
    cash, shares = capital, np.zeros(30)
    vals = [capital]

    def step(px, n, day, daily):
        nonlocal cash, shares, traded
        value = cash + shares @ px
        w = shares * px / value
        obs = {"symbols": list(SY), "phase": "validation",
               "portfolio": {"positions": {s: float(q) for s, q in zip(SY, shares) if q > 0},
                             "weights": {s: float(x) for s, x in zip(SY, w)}, "cash": cash, "value": value},
               "round": {"number": n, "id": f"validation-{day.date()}-r{n}", "day": str(day.date())},
               "as_of": pd.Timestamp(day) + pd.Timedelta(hours=8 + n, minutes=30 if n == 1 else 25),
               "daily_close": daily, "window_start": str(days[0].date()), "_daily": daily}
        tgt = fn(obs)
        if tgt is not None:
            t = np.array([max(0.0, float(tgt.get(s, 0.0))) for s in SY])
            if t.sum() > 1:
                t = t / t.sum()
            new_sh = t * value / px
            order = np.abs(new_sh - shares) * px
            traded += order.sum() / value
            cash = cash + (shares - new_sh) @ px - order.sum() * cost_bps / 1e4
            shares = new_sh

    for day in days:
        pos = sim.CLOSE.index.get_loc(day)
        daily = sim.CLOSE.iloc[max(0, pos - 420):pos]
        step(sim.OPEN.loc[day].values, 1, day, daily)
        vals.append(cash + shares @ sim.OPEN.loc[day].values)
        mk = sim.marks(day)
        for i, row in enumerate(mk):
            if intraday and i < len(mk) - 1 and i < 6:
                step(np.asarray(row), i + 2, day, daily)        # round i+2 executes at this hourly price
            vals.append(cash + shares @ np.asarray(row))
    sim.LAST_TURNOVER[0] = traded
    return np.array(vals)


# ----------------------------------------------------------------------------------- generic competitors
def _ew(level, rebalance_every_round=False, name=None):
    def f(obs):
        if obs["portfolio"]["positions"] and not rebalance_every_round:
            return None
        return {s: level / 30 for s in obs["symbols"]}
    f.name = name or f"EW {int(level*100)}% buy & hold"
    return f


def _mom(level=1.0, k=10):
    def f(obs):
        if obs["round"]["number"] != 1:
            return None
        d = obs["_daily"]
        if len(d) < 253:
            return None
        m = d.iloc[-22].values / d.iloc[-253].values - 1
        top = np.argsort(-m)[:k]
        cur = np.array([obs["portfolio"]["weights"].get(s, 0.0) for s in SY])
        t = np.zeros(30); t[top] = level / k
        if obs["portfolio"]["positions"] and np.abs(t - cur).sum() < 0.2:
            return None
        return dict(zip(SY, t.tolist()))
    f.name = f"Momentum top{k} {int(level*100)}%"
    return f


def _revert(level=0.6, k=8):
    def f(obs):
        if obs["round"]["number"] != 1:
            return None
        d = obs["_daily"]
        r5 = d.iloc[-1].values / d.iloc[-6].values - 1
        t = np.zeros(30); t[np.argsort(r5)[:k]] = level / k
        return dict(zip(SY, t.tolist()))
    f.name = f"Mean reversion 5d {int(level*100)}%"
    return f


def _voltgt(target=0.10):
    def f(obs):
        if obs["round"]["number"] != 1:
            return None
        d = obs["_daily"]
        ew = d.pct_change().iloc[-20:].mean(1)
        S = float(np.clip(target / max(ew.std() * np.sqrt(252), 1e-6), 0.1, 1.0))
        cur = sum(obs["portfolio"]["weights"].values())
        if obs["portfolio"]["positions"] and abs(S - cur) < 0.1:
            return None
        return {s: S / 30 for s in SY}
    f.name = f"Vol-target EW {int(target*100)}%"
    return f


def _nearcash(level=2e-5):
    def f(obs):
        if obs["portfolio"]["positions"]:
            return None
        return {s: level / 30 for s in SY}
    f.name = f"Near-cash EW {level:.0e}"
    return f


def generic():
    out = [sim.bench_cash, _nearcash(2e-5), _nearcash(2e-4), _ew(0.3), _ew(0.6),
           _ew(1.0, True, "EW 100% every-round rebalance"), _mom(1.0), _mom(0.6, 15), _revert(),
           _voltgt(0.10), _voltgt(0.15), sim.bench_losers, sim.bench_winners]
    return {f.name: (f, None) for f in out}


def ours():
    e = {k: v for k, v in field2.fixed().items() if k != "BreadthGuard v1"}
    m3 = sim.load_module(os.path.join(ST, "Combined_V3.py"), "f5_v3_" + str(os.getpid()))
    m4 = sim.load_module(os.path.join(ST, "Combined_V4.py"), "f5_v4_" + str(os.getpid()))
    e["Combined_V3"] = (m3.make_rule(), None)
    e["Combined_V4"] = (m4.strategy, None)
    return e


def entrants():
    return {**generic(), **ours()}


def run(fn, rs=None, wins=None, lab=""):
    wins = wins if wins is not None else WINS
    cost = field2.BENCH_COST.get(lab, COST)
    if lab == "Kit example (recent winners)":
        cost = 30.0
    return [sim.metrics(run_window_rounds(fn, d, cost, rs)) for d in wins]


def _job(lab):
    fn, rs = entrants()[lab]
    return lab, run(fn, rs, WINS, lab), run(fn, rs, OCT_WINS, lab)


def field():
    p = os.path.join(sim.HERE, "_field5_cache.pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    out = {"all": {}, "oct": {}}
    with Pool(4) as pool:
        for lab, a, o in pool.imap_unordered(_job, list(entrants())):
            out["all"][lab], out["oct"][lab] = a, o
            print("done", lab, flush=True)
    pickle.dump(out, open(p, "wb"))
    return out


MET = field4.MET

if __name__ == "__main__":
    F = field()
    for k in ("all", "oct"):
        print(f"== {k}")
        print(field2.table(F[k], list(F[k]), MET).round(3).to_string())
