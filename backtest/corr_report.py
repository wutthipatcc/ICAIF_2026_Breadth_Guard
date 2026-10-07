"""Correlation review of the 30-stock universe (2022-02-01 .. 2025-12-31 daily returns)."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import sim

c = sim.CLOSE
r = c.pct_change().loc["2022-02-01":"2025-12-31"]
C = r.corr()
n = len(C)
off = C.values[~np.eye(n, dtype=bool)]
print(f"average pairwise correlation {off.mean():.3f} (median {np.median(off):.3f})\n")
print("average correlation to the other 29 names:")
print(((C.sum() - 1) / (n - 1)).sort_values().round(2).to_string(), "\n")
pairs = sorted((C.iloc[i, j], C.index[i], C.index[j]) for i in range(n) for j in range(i + 1, n))
print("most correlated pairs:", ", ".join(f"{a}/{b} {x:.2f}" for x, a, b in pairs[-10:][::-1]))
print("least correlated pairs:", ", ".join(f"{a}/{b} {x:.2f}" for x, a, b in pairs[:6]), "\n")

rr = c.pct_change()
roll = pd.Series([np.nanmean(rr.iloc[i - 63:i].corr().values[~np.eye(n, dtype=bool)]) for i in range(64, len(rr))],
                 index=rr.index[64:])
fwd = (1 + rr.mean(1)).rolling(15).apply(np.prod, raw=True).shift(-15) - 1
df = pd.DataFrame({"corr63": roll, "fwd15": fwd}).loc["2022-02-01":"2025-12-31"].dropna()
df["quartile"] = pd.qcut(df.corr63, 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
print("63-day average correlation regime vs next-15-day equal-weight return:")
print(df.groupby("quartile").agg(avg_corr=("corr63", "mean"), fwd_mean=("fwd15", "mean"), fwd_std=("fwd15", "std"),
                                 share_negative=("fwd15", lambda x: (x < 0).mean())).round(4).to_string())
