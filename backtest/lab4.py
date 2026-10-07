"""Combined_V4 research harness: sweep exposure / shock / weighting choices against the screenshot field (field4)."""
import warnings; warnings.filterwarnings("ignore")
import sys, json, numpy as np, pandas as pd
from multiprocessing import Pool
import os
import sim, sweep, field2, field4, lab3, bg_lab
VS_V1 = os.environ.get("VS_V1") == "1"

SY = sim.SYMBOLS


def _wday(obs, daily):
    start = pd.Timestamp(obs["window_start"])
    idx = pd.DatetimeIndex(daily.index)
    return int((idx >= start).sum())


def make(E0=1e-5, E1=2.4e-5, weight="iv", score="z_resmom", tilt=0.6, cutoff=10, shock_kind="breadth",
         mode="hold", miss=True, g=0.05, k=0.5, trend_off=False, voltgt=None, trend_zero=None, rearm=False, shock_thr=None, oversold=None, ivpow=1.0, cap_mult=100):
    def f(obs):
        port = obs["portfolio"]
        started = bool(port["positions"])
        daily = obs["_daily"].reindex(columns=SY)
        ft = lab3._feat(daily)
        cur = np.array([port["weights"].get(s, 0.0) for s in SY])
        shock = ft["shock_" + shock_kind]
        if shock_thr is not None:
            r1 = daily.iloc[-1].values / daily.iloc[-2].values - 1
            shock = bool(np.nanmean(r1) <= shock_thr and np.nanmean(r1 < 0) >= 0.65)
        lvl = cur.sum()
        switched = started and lvl > (E0 + E1) / 2
        ok_day = cutoff is None or _wday(obs, daily) <= cutoff
        if rearm:
            fire = bool(started and shock and ok_day and lvl * (E1 / E0) <= E0 * cap_mult * 1.01)
            S = lvl * (E1 / E0) if fire else max(lvl, E0)
        else:
            fire = bool(started and not switched and E1 > E0 and shock and ok_day)
            S = E1 if (switched or fire) else E0
        if oversold is not None and not started and ft["mkt_mom20"] < oversold:
            S = E1
        if trend_off and not started and (ft["mkt_ma100"] < 0):
            S = S * 0.5
        if voltgt and not started:
            S = S * float(np.clip(voltgt / max(ft["mkt_vol20"], 1e-6), 0.25, 4.0))
        if trend_zero and not started and ft[trend_zero] < 0:
            return dict(zip(SY, [0.0] * 30))
        z = ft[score] if score else np.zeros(30)
        if weight == "ew":
            b = np.full(30, 1 / 30)
        else:
            b = 1 / ft["vol60"] ** ivpow; b = b / b.sum()
        b = np.clip(b * (1 + tilt * z), 0, None)
        b = b / b.sum()
        t = np.minimum(S * b, 0.30)
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
    lab, kw = a
    return lab, field2.run_entrant(make(**kw), None, field4.SCEN)


_V1 = None


def v1_per():
    global _V1
    if _V1 is None:
        import os, pickle
        p = os.path.join(sim.HERE, "_v1_cache.pkl")
        if os.path.exists(p):
            _V1 = pickle.load(open(p, "rb"))
        else:
            m = sim.load_module(os.path.join(sim.ROOT, "strategies", "Combined_V1.py"), "l4_v1")
            _V1 = field2.run_entrant(m.strategy, None, field4.SCEN)
            pickle.dump(_V1, open(p, "wb"))
    return _V1


def report(lab, per, F):
    out = []
    for nm, labs in (("team", field4.TEAM), ("mock", field4.TEAM + field4.BENCH)):
        P = {**{l: F[l] for l in labs}, lab: per}
        for sub, idx in (("", None), ("22-23", sweep.TRAIN), ("24-25", sweep.TEST)):
            t = field2.table(P, list(P), field4.MET, idx)
            out.append(f"{nm}{sub}: {t.loc[lab,'avg_score']:.2f}/PT {t.loc['PairTrading V5.1','avg_score']:.2f} #{list(t.index).index(lab)+1}")
        if VS_V1:
            P = {**{l: F[l] for l in labs}, "V1": v1_per(), lab: per}
            t = field2.table(P, list(P), field4.MET)
            out.append(f"{nm}+V1: {t.loc[lab,'avg_score']:.2f} vs V1 {t.loc['V1','avg_score']:.2f}")
    r = np.mean([m["return"] for m in per]) * 100
    st = np.mean([m["stability"] for m in per])
    return f"{lab:34s} ret {r:.4f}% stab {st:.3f} | " + " | ".join(out)


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    F = field4.field()
    with Pool(4) as p:
        for lab, per in p.imap_unordered(one, list(cfg.items())):
            print(report(lab, per, F), flush=True)
