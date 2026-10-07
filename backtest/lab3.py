"""Candidate family for an agent that out-ranks both PairTrading and Cash (research harness)."""
import warnings; warnings.filterwarnings("ignore")
import os, sys, json, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep, field2, bg_lab

SY = sim.SYMBOLS
_JM = sim.load_module(os.path.join(sim.ROOT, "strategies", "jimin_test_v5.py"), "lab3_jm")
_C = {}


def _feat(daily):
    key = daily.index[-1]
    if key in _C:
        return _C[key]
    n = 30
    r = daily.pct_change().iloc[1:]
    ew = r.mean(1)
    idx = (1 + ew).cumprod()
    f = {
        "z_rank": bg_lab._signal_rank_tuned(daily, n),
        "z_lowvol": -bg_lab._zscore(r.iloc[-60:].std().values),
        "mv": bg_lab._min_var_raw(daily, 126, 0.5, 0.10, 300),
        "vol60": r.iloc[-60:].std().values,
        "mkt_ma100": float(idx.iloc[-1] / idx.iloc[-100:].mean() - 1),
        "mkt_mom20": float(idx.iloc[-1] / idx.iloc[-21] - 1),
        "mkt_vol20": float(ew.iloc[-20:].std() * np.sqrt(252)),
        "shock_breadth": bg_lab._shock_yesterday(daily),
        "shock_mean": bg_lab._shock_yesterday_v4(daily),
    }
    rm = _JM.residual_momentum(daily)
    f["z_resmom"] = bg_lab._zscore(rm) if rm is not None else f["z_rank"]
    f["z_mix"] = bg_lab._zscore(0.5 * f["z_rank"] + 0.5 * f["z_resmom"])
    _C[key] = f
    return f


def make(E=1e-5, K=30, weight="ew", score="z_rank", tilt=0.6, mode="band", shock_mult=2.4, shock_kind="breadth",
         gate=None, miss=True, k=0.5, g=0.05):
    def f(obs):
        port = obs["portfolio"]
        started = bool(port["positions"])
        if started and obs["round"]["number"] != 1:
            return None
        daily = obs["_daily"].reindex(columns=SY)
        ft = _feat(daily)
        cur = np.array([port["weights"].get(s, 0.0) for s in SY])
        S0, S1 = E, E * shock_mult if shock_mult else None
        if gate == "trend" and (ft["mkt_ma100"] < 0 or ft["mkt_mom20"] < 0) and not started:
            return None                                          # stay flat (exactly cash) until risk-on
        switched = S1 is not None and started and cur.sum() > (S0 + S1) / 2
        fire = bool(S1 is not None and started and not switched and ft["shock_" + shock_kind])
        S = S1 if (switched or fire) else S0
        z = ft[score] if score else np.zeros(30)
        if weight == "ew":
            b = np.full(30, 1 / 30)
        elif weight == "mv":
            b = ft["mv"].copy()
        else:
            b = 1 / ft["vol60"]; b = b / b.sum()
        b = np.clip(b * (1 + tilt * z), 0, None) if score else b
        if K < 30:
            keep = np.argsort(-(z if score else -ft["vol60"]))[:K]
            m = np.zeros(30, bool); m[keep] = True
            b = np.where(m, b, 0.0)
        b = b / b.sum()
        t = S * b
        excl = bg_lab._excluded(obs, daily, SY) if miss else np.zeros(30, bool)
        t[excl] = 0.0
        if not started or fire:
            new = t
        elif mode == "hold":
            if not (excl & (cur > 0)).any():
                return None
            new = cur.copy(); new[excl] = 0.0
        else:
            must = bool((excl & (cur > 0)).any())
            if np.abs(t - cur).sum() < g * max(S, cur.sum()) / 0.25 and not must:
                return None
            new = cur + k * (t - cur); new[excl] = 0.0
        return dict(zip(SY, new.tolist()))
    return f


def one(a):
    lab, kw, scen = a
    return lab, scen, field2.run_entrant(make(**kw), None, scen)


def report(lab, per_by_scen, idx_sets=(("all", None), ("22-23", sweep.TRAIN), ("24-25", sweep.TEST))):
    F = field2.field()
    m = field2.METRICS["ret+stab+maxdd+trading"]
    parts = []
    for scen, per in per_by_scen.items():
        P = {**F[scen], lab: per}
        for nm, idx in idx_sets:
            t = field2.table(P, list(P), m, idx)
            parts.append(f"{scen[:1]}{nm}: {t.loc[lab,'avg_score']:.2f} (PT {t.loc['PairTrading V5.1','avg_score']:.2f} cash {t.loc['Cash only','avg_score']:.2f} #{list(t.index).index(lab)+1})")
    return f"{lab:44s} " + " | ".join(parts)


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    scens = sys.argv[2].split(",") if len(sys.argv) > 2 else ["B"]
    scens = [s for s in field2.SCEN if s[0] in scens]
    store = os.path.join(sim.HERE, "_lab3_cache.pkl")
    done = pickle.load(open(store, "rb")) if os.path.exists(store) else {}
    jobs = [(l, kw, s) for l, kw in cfg.items() for s in scens]
    res = {}
    with Pool(4) as p:
        for lab, scen, per in p.imap_unordered(one, jobs):
            res.setdefault(lab, {})[scen] = per
            done[(lab, scen)] = per
            if len(res[lab]) == len(scens):
                print(report(lab, res[lab]), flush=True)
    pickle.dump(done, open(store, "wb"))
