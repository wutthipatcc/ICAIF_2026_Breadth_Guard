"""Run Combined_V1 in the official ICAIF 2026 kit, uploading a decision only when the agent trades.

Copy this file and Combined_V1.py into the starter-kit root (next to tools/ and kit/), set up .env and
.icaif/credentials.json as in the kit README, then:

    python run_combined_v1.py --phase validation --once      # one pass: submit if the current round needs a trade
    python run_combined_v1.py --phase official                # keep running until the phase ends

A round where the agent holds gets no upload: per docs/rules.md the round then "performs no rebalance, charges no
transaction fee, and keeps the existing holdings" - zero turnover, unlike re-submitting weights.
State (the last uploaded target per phase, no secrets) is kept in .icaif/combined_v1_state.json.
"""
import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit.config import load_environment
from kit.contracts import dumps_json, timestamp
from kit.original_client import OriginalSession, load_profile

import Combined_V1 as agent


def one_pass(client, phase, refreshed):
    schedule = client.schedule()
    now = client._now(schedule)
    rows = [r for r in schedule["rounds"] if r["phase"] == phase and r["status"] != "CANCELLED"]
    if rows and now >= max(timestamp(r["close_time"]) for r in rows):
        return "PHASE_COMPLETE"
    row = next((r for r in rows if timestamp(r["opens_at"]) <= now < timestamp(r["deadline"])), None)
    if row is None:
        return "WAITING"
    own = client.round(row["id"])
    if client._occupied(own):
        return "ALREADY_SUBMITTED " + row["id"]
    if row["number"] == 1 and refreshed.get("day") != row["day"]:
        try:
            print("earnings misses added:", agent.refresh_misses(row["day"]))
        except Exception as error:                        # keep trading on the stored table
            print("earnings refresh skipped:", type(error).__name__)
        refreshed["day"] = row["day"]
    observation = {"phase": phase, "round": row, "symbols": schedule["symbols"], "as_of": now.isoformat(),
                   "portfolio": client.portfolio(phase), "round_state": own}
    weights = agent.kit_decide(observation)
    if weights is None:
        return "HOLD (no upload) " + row["id"]
    creds = client._team()
    payload = {"submission_type": "decision", "team_id": creds["team_id"], "team_token": creds["team_token"],
               "phase": phase, "round_id": row["id"], "weights": weights}
    result = client._decision(dumps_json(payload).encode("utf-8"), payload)
    status = str(result.get("validation_status") or result.get("status"))
    if "INVALID" not in status and "LATE" not in status:
        agent.save_state(phase, weights, row["id"])
    return f"SUBMITTED {row['id']} sleeve={sum(weights.values()):.2e} status={status}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--phase", choices=["validation", "official"], required=True)
    p.add_argument("--profile", default=os.environ.get("ICAIF_PROFILE"))
    p.add_argument("--once", action="store_true")
    p.add_argument("--poll-seconds", type=int, default=60)
    a = p.parse_args()
    load_environment()
    profile = a.profile or os.environ.get("ICAIF_PROFILE")
    with OriginalSession(profile=load_profile(profile), token=os.environ["CODABENCH_TOKEN"],
                         checkpoint=".icaif/checkpoint.json", credentials=".icaif/credentials.json") as client:
        refreshed, last = {}, None
        while True:
            msg = one_pass(client, a.phase, refreshed)
            if msg != last:
                print(datetime.now(timezone.utc).isoformat(timespec="seconds"), msg, flush=True)
                last = msg
            if a.once or msg == "PHASE_COMPLETE":
                break
            time.sleep(a.poll_seconds)


if __name__ == "__main__":
    main()
