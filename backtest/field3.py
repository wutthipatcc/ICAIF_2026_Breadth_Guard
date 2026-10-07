"""A synthetic ~50-team Official field, to rank candidates the way the competition does (one rank per metric over all
teams: cumulative return, Sharpe, max drawdown, turnover; equal weights; exact ties share ranks).

The real field is unknown, so three random fields are drawn from a broad mix of plausible entries:
  * inactive / all-cash teams (they never submit; a missing decision holds the 1M cash),
  * PairTrading-style near-cash teams,
  * generic agents: exposure 5%..100%, style (equal weight, 12-1 or 1-month momentum top-k, low-vol, inverse-vol,
    1-day reversal, random top-k), rebalanced once, daily, or daily with high churn.
Every window is scored over the 65 replica windows (fees 10 bp, fractional shares, no per-order floor).
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep

SY = sim.SYMBOLS
HIGHER = {"return": True, "stability": True, "maxdd": False, "trading": False}
METS = ("return", "stability", "maxdd", "trading")
_F = {}


def _sig(daily):
    k = daily.index[-1]
    if k not in _F:
        r = daily.pct_change().iloc[1:]
        _F[k] = {
            "mom121": (daily.iloc[-22] / daily.iloc[-253] - 1).values,
            "mom20": (daily.iloc[-1] / daily.iloc[-21] - 1).values,
            "lowvol": -r.iloc[-60:].std().values,
            "rev1": -(daily.iloc[-1] / daily.iloc[-2] - 1).values,
            "iv": 1 / r.iloc[-60:].std().values,
        }
    return _F[k]


def generic(E, style, k, rebal, seed=0):
    rng = np.random.default_rng(seed)
    fixed_pick = rng.choice(30, k, replace=False)

    def f(obs):
        started = bool(obs["portfolio"]["positions"])
        if started and rebal == "once":
            return None
        s = _sig(obs["_daily"])
        w = np.zeros(30)
        if style == "ew":
            w[:] = 1.0
        elif style == "iv":
            w = s["iv"].copy()
        elif style == "random":
            w[fixed_pick] = 1.0
        else:
            w[np.argsort(-s[style])[:k]] = 1.0
        w = E * w / w.sum()
        w = np.minimum(w, 0.30)
        return dict(zip(SY, w.tolist()))
    return f


def near_cash(E, mult):
    state = {}

    def f(obs):
        started = bool(obs["portfolio"]["positions"])
        d = obs["_daily"]
        if not started:
            state["boost"] = False
        if started and float((d.iloc[-1] / d.iloc[-2] - 1).mean()) <= -0.02:
            state["boost"] = True
        e = E * (mult if state.get("boost") else 1.0)
        return dict(zip(SY, [e / 30] * 30))
    return f


def draw_field(seed, n_generic=40, n_cash=4, n_nearcash=3):
    rng = np.random.default_rng(seed)
    teams = {}
    for i in range(n_cash):
        teams[f"cash{i}"] = ("cash", {})
    for i in range(n_nearcash):
        teams[f"nearcash{i}"] = ("near", dict(E=float(10 ** rng.uniform(-4.5, -2)), mult=float(rng.choice([1, 10, 50]))))
    styles = ["ew", "mom121", "mom20", "lowvol", "iv", "rev1", "random"]
    for i in range(n_generic):
        teams[f"g{i}"] = ("gen", dict(E=float(rng.choice([0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0])),
                                     style=str(rng.choice(styles)), k=int(rng.choice([5, 10, 15])),
                                     rebal=str(rng.choice(["once", "daily", "daily"])), seed=int(rng.integers(1e9))))
    return teams


def build(kind, kw):
    if kind == "cash":
        return sim.bench_cash
    if kind == "near":
        return near_cash(**kw)
    return generic(**kw)


def run(args):
    name, kind, kw = args
    cost = 60.0 if (kind == "gen" and kw.get("style") in ("rev1", "mom20") and kw.get("rebal") == "daily") else 10.0
    fn = build(kind, kw)
    return name, [sim.metrics(sim.run_window(fn, d, cost)) for d in sweep.W]


def field(seed):
    p = os.path.join(sim.HERE, f"_field3_{seed}.pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    teams = draw_field(seed)
    with Pool(4) as pool:
        per = dict(pool.map(run, [(n, k, kw) for n, (k, kw) in teams.items()]))
    # the team's own competitors as they would also appear in the field
    pickle.dump(per, open(p, "wb"))
    return per


def place(per, cand, idx=None):
    """Average overall rank score and average finishing position of `cand` across windows."""
    labs = list(per)
    nw = len(per[labs[0]])
    idx = range(nw) if idx is None else idx
    sc, pos = [], []
    for i in idx:
        R = np.vstack([sim._rank([per[l][i][m] for l in labs], HIGHER[m]) for m in METS]).mean(0)
        j = labs.index(cand)
        sc.append(R[j])
        pos.append(1 + (R < R[j]).sum())
    return np.mean(sc), np.mean(pos), np.mean(np.array(pos) <= 3)
