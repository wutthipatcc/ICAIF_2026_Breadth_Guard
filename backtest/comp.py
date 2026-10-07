"""Fast research on portfolio composition: precompute daily target weights, then simulate."""
import warnings; warnings.filterwarnings("ignore")
import sys, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, field, sweep, bg_lab

C = sim.CLOSE
DAYS = [d for w in sweep.W for d in w]


def feats(day):
    pos = C.index.get_loc(day)
    daily = C.iloc[pos - 253:pos]
    n = 30
    r = daily.pct_change().iloc[1:]
    f = {}
    f["ew"] = np.full(n, 1 / n)
    for win, sh, cap in [(126, 0.5, 0.10), (63, 0.5, 0.10), (252, 0.5, 0.10), (126, 0.2, 0.10), (126, 0.8, 0.10), (126, 0.5, 0.06)]:
        f[f"mv{win}_{sh}_{cap}"] = bg_lab._min_var_raw(daily, win, sh, cap, 300)
    iv = 1 / r.iloc[-63:].std().values
    f["invvol"] = iv / iv.sum()
    corr = r.iloc[-126:].corr().values
    avgc = (corr.sum(1) - 1) / (n - 1)
    ivc = iv / np.maximum(avgc, 0.05)
    f["invvolcorr"] = ivc / ivc.sum()
    f["z_rank"] = bg_lab._signal_rank_tuned(daily, n)
    f["z_mom"] = bg_lab._zscore(daily.iloc[-22].values / daily.iloc[-253].values - 1)
    f["z_lowvol"] = -bg_lab._zscore(r.iloc[-60:].std().values)
    f["z_st_rev"] = -bg_lab._zscore(daily.iloc[-1].values / daily.iloc[-6].values - 1)
    f["z_mom3"] = bg_lab._zscore(daily.iloc[-1].values / daily.iloc[-64].values - 1)
    ew = r.mean(1)
    f["mkt_vol20"] = ew.iloc[-20:].std() * np.sqrt(252)
    f["mkt_corr63"] = (r.iloc[-63:].corr().values.sum() - n) / (n * (n - 1))
    idx = (1 + ew).cumprod()
    f["mkt_ma100"] = idx.iloc[-1] / idx.iloc[-100:].mean() - 1
    f["mkt_mom20"] = idx.iloc[-1] / idx.iloc[-21] - 1
    return day, f


def build():
    with Pool(4) as p:
        F = dict(p.map(feats, DAYS, chunksize=20))
    pickle.dump(F, open("_feats.pkl", "wb"))
    return F


if __name__ == "__main__":
    build()
    print("ok")
