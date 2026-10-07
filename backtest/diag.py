import warnings; warnings.filterwarnings("ignore")
import sys, pickle, numpy as np, pandas as pd
import sim, field
cand = pickle.load(open("_cand_cache.pkl", "rb"))
base = field.field()
labs = sys.argv[1:]
for lab in labs:
    per = {**base, lab: cand[lab]}
    L = list(per); nw = len(per[L[0]])
    R = {k: np.zeros((nw, len(L))) for k in ["return", "stability", "maxdd", "vol"]}
    for i in range(nw):
        m = [per[l][i] for l in L]
        R["return"][i] = sim._rank([x["return"] for x in m], True)
        R["stability"][i] = sim._rank([x["stability"] for x in m], True)
        R["maxdd"][i] = sim._rank([x["maxdd"] for x in m], False)
        R["vol"][i] = sim._rank([x["vol"] for x in m], False)
    df = pd.DataFrame({k: v.mean(0) for k, v in R.items()}, index=L)
    df["score"] = df.mean(1)
    print(lab); print(df.round(2).sort_values("score").to_string()); print()
