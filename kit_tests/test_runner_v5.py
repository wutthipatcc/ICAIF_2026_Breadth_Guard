# Run from a copy of the official starter-kit root that also contains Combined_V5.py and run_combined_v5.py.
import os, sys, types
os.environ["COMBINED_V5_STATE"] = "state_runner_v5.json"
if os.path.exists("state_runner_v5.json"): os.remove("state_runner_v5.json")
os.environ["CODABENCH_TOKEN"] = "x"
import run_combined_v5 as R

class FakeClient:
    def __init__(self, day, n): self.day, self.n, self.uploads = day, n, []
    def schedule(self):
        rows = [{"id": f"validation-{self.day}-r{k}", "phase": "validation", "day": self.day, "number": k, "status": "SCHEDULED",
                 "opens_at": f"{self.day}T00:00:00+00:00" if k == self.n else "2000-01-01T00:00:00+00:00",
                 "deadline": f"{self.day}T23:00:00+00:00" if k == self.n else "2000-01-01T01:00:00+00:00",
                 "close_time": "2099-01-01T00:00:00+00:00", "execution_time": "2099-01-01T00:00:00+00:00"} for k in range(1, 8)]
        return {"rounds": rows, "symbols": R.agent.UNIVERSE, "current_time": f"{self.day}T12:00:00+00:00"}
    def _now(self, s):
        from kit.contracts import timestamp; return timestamp(s["current_time"])
    def round(self, rid): return {"decisions": []}
    _occupied = staticmethod(lambda own: False)
    def portfolio(self, phase): return {}
    def _team(self): return {"team_id": "t", "team_token": "x"}
    def _decision(self, raw, payload): self.uploads.append(payload["round_id"]); return {"status": "PENDING", "validation_status": "VALID"}

R.agent.refresh_misses = lambda day: 0              # earnings refresh tested separately (network)
for day, n in [("2026-10-08", 1), ("2026-10-08", 2), ("2026-10-09", 1)]:
    c = FakeClient(day, n)
    print(day, "r%d" % n, "->", R.one_pass(c, "validation", {}), "| uploads", c.uploads)
