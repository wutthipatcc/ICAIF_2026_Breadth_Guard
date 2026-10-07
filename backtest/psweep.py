"""Parallel candidate sweep: python3 psweep.py <configs.json> -> prints one line per config, saves metrics."""
import warnings; warnings.filterwarnings("ignore")
import sys, json, pickle, os
from multiprocessing import Pool
import numpy as np
import sim, field, bg_lab, sweep


def one(item):
    label, kw = item
    fn = bg_lab.make(**kw)
    return label, [sim.metrics(sim.run_window(fn, d)) for d in sweep.W]


def report(label, per):
    out = {}
    for nm, idx in (("all", None), ("train", sweep.TRAIN), ("test", sweep.TEST)):
        t = field.score({label: per}, idx)
        out[nm] = (t.loc[label, "avg_score"], t.loc["Cash only", "avg_score"], list(t.index).index(label) + 1)
    r = np.mean([m["return"] for m in per]) * 100
    return (f"{label:58s} all {out['all'][0]:.3f} (cash {out['all'][1]:.3f}, #{out['all'][2]})  "
            f"train {out['train'][0]:.3f}/{out['train'][1]:.3f}  test {out['test'][0]:.3f}/{out['test'][1]:.3f}  ret {r:.3f}%")


if __name__ == "__main__":
    field.field()
    cfg = json.load(open(sys.argv[1]))
    items = list(cfg.items())
    store = os.path.join(sim.HERE, "_cand_cache.pkl")
    done = pickle.load(open(store, "rb")) if os.path.exists(store) else {}
    with Pool(4) as p:
        for label, per in p.imap_unordered(one, items):
            done[label] = per
            print(report(label, per), flush=True)
    pickle.dump(done, open(store, "wb"))
