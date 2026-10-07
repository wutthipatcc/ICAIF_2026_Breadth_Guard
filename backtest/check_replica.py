"""Does the local evaluator reproduce the web tool's rankings (screenshots)?"""
import time
import sim, entrants
t = time.time()
E = entrants.team() + entrants.bench()
per = sim.evaluate(E)
labs = [e[0] for e in E]
print(len(sim.windows()), "windows", round(time.time() - t), "s")
print(sim.rank_summary(per, labs[:3]).round(2).to_string())
print(sim.rank_summary(per, labs).round(2).to_string())
