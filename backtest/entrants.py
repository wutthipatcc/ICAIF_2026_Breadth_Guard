"""Builds the entrant list: the three team strategies plus the four benchmarks."""
import os
import sim

S = os.path.join(sim.ROOT, "strategies")


def team(extra=()):
    bg = sim.load_module(os.path.join(S, "BreadthGuard_v1.py"), "bg_v1")
    jm = sim.load_module(os.path.join(S, "jimin_test_v5.py"), "jimin_v5")
    pt = sim.load_module(os.path.join(S, "pairtrading_v5_1_500.py"), "pt_v51")
    out = [("PairTrading V5.1", pt.strategy, pt.reset),
           ("jimin_test_v5", jm.strategy, lambda: jm._START.clear()),
           ("BreadthGuard v1", bg.strategy, None)]
    return out + list(extra)


def bench():
    return [(f.name, f, None) for f in sim.BENCHMARKS]
