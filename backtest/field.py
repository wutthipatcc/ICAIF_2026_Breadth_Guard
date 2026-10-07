"""Caches the fixed field (PairTrading, jimin, benchmarks) so candidates can be scored quickly."""
import os, pickle
import sim, entrants

CACHE = os.path.join(sim.HERE, "_field_cache.pkl")


def field():
    if os.path.exists(CACHE):
        return pickle.load(open(CACHE, "rb"))
    E = [e for e in entrants.team() if e[0] != "BreadthGuard v1"] + entrants.bench()
    per = sim.evaluate(E)
    pickle.dump(per, open(CACHE, "wb"))
    return per


def score(cand_per, wins_idx=None, weights=(1, 1, 1, 1)):
    """cand_per: {label: [metrics per window]} for candidate(s); returns mock-competition table."""
    base = field()
    per = {**base, **cand_per}
    if wins_idx is not None:
        per = {k: [v[i] for i in wins_idx] for k, v in per.items()}
    return sim.rank_summary(per, list(per), weights)
