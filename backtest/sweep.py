import sys, itertools, json
import numpy as np
import sim, field, bg_lab

W = sim.windows()
TRAIN = [i for i, d in enumerate(W) if d[0] < np.datetime64("2024-01-01")]
TEST = [i for i, d in enumerate(W) if d[0] >= np.datetime64("2024-01-01")]


def run(label, fn):
    per = {label: [sim.metrics(sim.run_window(fn, d)) for d in W]}
    out = {}
    for nm, idx in (("all", None), ("train", TRAIN), ("test", TEST)):
        t = field.score(per, idx)
        out[nm] = (t.loc[label, "avg_score"], t.loc["Cash only", "avg_score"], int(list(t.index).index(label)) + 1)
    r = np.mean([m["return"] for m in per[label]]) * 100
    print(f"{label:60s} all {out['all'][0]:.2f} (cash {out['all'][1]:.2f}, #{out['all'][2]})  "
          f"train {out['train'][0]:.2f}/{out['train'][1]:.2f}  test {out['test'][0]:.2f}/{out['test'][1]:.2f}  ret {r:.2f}%", flush=True)
    return per
