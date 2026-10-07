"""Which 4 metrics does the web scorer rank? Compare candidate metric sets with the web tables (2026-10-07 run)."""
import warnings; warnings.filterwarnings("ignore")
import os, pickle, itertools, numpy as np, pandas as pd
from multiprocessing import Pool
import sim, sweep

S = os.path.join(sim.ROOT, "strategies")
CACHE = os.path.join(sim.HERE, "_calib_cache.pkl")


def ents():
    v1 = sim.load_module(os.path.join(S, "BreadthGuard_v1.py"), "c_v1")
    v2 = sim.load_module(os.path.join(S, "BreadthGuard_v2.py"), "c_v2")
    pt = sim.load_module(os.path.join(S, "pairtrading_v5_1_500.py"), "c_pt")
    jm = sim.load_module(os.path.join(S, "jimin_test_v5.py"), "c_jm")
    e = {"PT": (pt.strategy, pt.reset), "v2": (v2.strategy, None), "jimin": (jm.strategy, lambda: jm._START.clear()),
         "v1": (v1.strategy, None), "cash": (sim.bench_cash, None), "ew": (sim.bench_ew, None),
         "losers": (sim.bench_losers, None), "winners": (sim.bench_winners, None)}
    return e


def one(lab):
    fn, rs = ents()[lab]
    return lab, [sim.metrics(sim.run_window(fn, d, 2.0, rs)) for d in sweep.W]


WEB_TEAM = {"PT": 1.91, "v2": 2.24, "jimin": 2.89, "v1": 2.97}
WEB_MOCK = {"PT": 2.99, "cash": 3.15, "v2": 3.29, "jimin": 3.92, "v1": 4.00, "ew": 4.77, "losers": 6.14, "winners": 7.73}
HIGHER = {"return": True, "stability": True, "maxdd": False, "vol": False, "worst": False, "trading": False}


def scores(per, labs, mets, w=None):
    w = np.ones(len(mets)) if w is None else np.asarray(w, float)
    nw = len(per[labs[0]])
    tot = np.zeros(len(labs))
    for i in range(nw):
        R = np.vstack([sim._rank([per[l][i][m] for l in labs], HIGHER[m]) for m in mets])
        tot += (R * w[:, None]).sum(0) / w.sum()
    return dict(zip(labs, tot / nw))


if __name__ == "__main__":
    if os.path.exists(CACHE):
        per = pickle.load(open(CACHE, "rb"))
    else:
        with Pool(4) as p:
            per = dict(p.map(one, list(ents())))
        pickle.dump(per, open(CACHE, "wb"))
    for l in per:
        print(f"{l:8s} trading {np.mean([m['trading'] for m in per[l]]):.4f}  worst {100*np.mean([m['worst'] for m in per[l]]):.2f}%  "
              f"maxdd {100*np.mean([m['maxdd'] for m in per[l]]):.2f}%  ret {100*np.mean([m['return'] for m in per[l]]):.2f}%")
    rows = []
    allm = ["return", "stability", "maxdd", "vol", "worst", "trading"]
    for k in (3, 4, 5):
        for mets in itertools.combinations(allm, k):
            for w in ([1] * k, ([0.616, 0.616] + [1] * (k - 2)) if mets[:2] == ("return", "stability") else None):
                if w is None:
                    continue
                t = scores(per, list(WEB_TEAM), mets, w)
                m = scores(per, list(WEB_MOCK), mets, w)
                et = np.sqrt(np.mean([(t[l] - WEB_TEAM[l]) ** 2 for l in WEB_TEAM]))
                em = np.sqrt(np.mean([(m[l] - WEB_MOCK[l]) ** 2 for l in ["PT", "cash", "v2", "jimin", "v1"]]))
                rows.append((et, em, "+".join(mets), "w" if w[0] != 1 else "eq",
                             " ".join(f"{t[l]:.2f}" for l in WEB_TEAM), " ".join(f"{m[l]:.2f}" for l in ["PT", "cash", "v2", "jimin", "v1"])))
    df = pd.DataFrame(rows, columns=["rmse_team", "rmse_mock5", "metrics", "wts", "team PT v2 jim v1", "mock PT cash v2 jim v1"])
    df["tot"] = df.rmse_team + df.rmse_mock5
    print("web team:", WEB_TEAM, "\nweb mock:", WEB_MOCK)
    print(df.sort_values("tot").head(15).round(3).to_string(index=False))
