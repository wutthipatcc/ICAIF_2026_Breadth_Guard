import warnings; warnings.filterwarnings("ignore")
import sys, pickle, json, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, field, sweep, bg_lab

F = pickle.load(open("_feats.pkl", "rb"))
SY = sim.SYMBOLS
EXCL = {}


def excl(day):
    if day not in EXCL:
        pos = sim.CLOSE.index.get_loc(day)
        obs = {"round": {"id": f"validation-{day.date()}-r1"}}
        EXCL[day] = bg_lab._excluded(obs, sim.CLOSE.iloc[pos - 30:pos], SY)
    return EXCL[day]


def make(S=0.1, base="ew", z=None, tilt=0.0, S1=None, k=0.5, g=0.05, gate=None, vt=None, shock_breadth=True,
         tp=None, sl=None, cap0=1_000_000.0, exit_frac=0.0):
    state = {}
    def f(obs):
        ws = obs["window_start"]
        if state.get("ws") != ws:
            state.clear(); state["ws"] = ws
        pnl = obs["portfolio"]["value"] / cap0 - 1
        if state.get("out") or (obs["portfolio"]["positions"] and ((tp is not None and pnl >= tp) or (sl is not None and pnl <= -sl))):
            first = not state.get("out")
            state["out"] = True
            if first:
                cur = np.array([obs["portfolio"]["weights"].get(s, 0.0) for s in SY])
                return dict(zip(SY, (cur * exit_frac).tolist()))
            return None
        day = pd.Timestamp(obs["round"]["id"].split("-r")[0].split("-", 1)[1])
        ft = F[day]
        port = obs["portfolio"]
        started = bool(port["positions"])
        cur = np.array([port["weights"].get(s, 0.0) for s in SY])
        s = S
        if vt is not None:
            s = S * min(1.5, vt / max(ft["mkt_vol20"], 1e-6))
        if gate == "ma" and ft["mkt_ma100"] < 0:
            s = 0.0
        if gate == "corr" and ft["mkt_corr63"] > 0.40:
            s = s * 0.5
        fire = False
        if S1 is not None and started and s > 0:
            switched = cur.sum() > s * (1 + S1) / 2
            daily = obs["_daily"]
            fire = (not switched) and (bg_lab._shock_yesterday(daily) if shock_breadth else bg_lab._shock_yesterday_v4(daily))
            if switched or fire:
                s = s * S1
        b = ft[base].copy()
        if z is not None and tilt:
            zz = sum(wt * ft[name] for name, wt in z.items())
            b = np.clip(b + tilt * zz / 30, 0, None)
            b = b / b.sum()
        t = s * b
        t = np.minimum(t, 0.30)
        e = excl(day)
        t[e] = 0.0
        if not started or fire or (s == 0 and cur.sum() > 0):
            new = t
        else:
            if np.abs(t - cur).sum() < g * max(s, cur.sum(), 1e-9) / 0.25 and not (e & (cur > 1e-6)).any():
                return None
            new = cur + k * (t - cur)
            new[e] = 0.0
        return dict(zip(SY, new.tolist()))
    return f


def one(item):
    lab, kw = item
    fn = make(**kw)
    return lab, [sim.metrics(sim.run_window(fn, d)) for d in sweep.W]


def rep(lab, per):
    t = field.score({lab: per}); tr = field.score({lab: per}, sweep.TRAIN); te = field.score({lab: per}, sweep.TEST)
    pos = np.mean([m["return"] > 0 for m in per])
    return (f"{lab:52s} all {t.loc[lab,'avg_score']:.3f}/{t.loc['Cash only','avg_score']:.3f} "
            f"train {tr.loc[lab,'avg_score']:.3f}/{tr.loc['Cash only','avg_score']:.3f} "
            f"test {te.loc[lab,'avg_score']:.3f}/{te.loc['Cash only','avg_score']:.3f}  win% {pos:.2f}  "
            f"ret {100*np.mean([m['return'] for m in per]):.3f}")


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    store = "_comp_cache.pkl"
    import os
    done = pickle.load(open(store, "rb")) if os.path.exists(store) else {}
    with Pool(4) as p:
        for lab, per in p.imap_unordered(one, list(cfg.items())):
            done[lab] = per
            print(rep(lab, per), flush=True)
    pickle.dump(done, open(store, "wb"))
