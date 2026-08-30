from __future__ import annotations

import json
import os
import sys


def main() -> None:
    request = json.load(sys.stdin)
    budget = request["budget"]
    score = float(os.environ.get("MATHARC_MOCK_SCORE", "0.5"))
    usage = {
        "tokens": min(int(budget["token_budget"]), 20),
        "model_calls": min(int(budget["model_call_budget"]), 1),
        "tool_cpu_seconds": min(float(budget["tool_cpu_seconds"]), 0.01),
    }
    payload = {
        "release_state": "PROVED_AND_AUDITED" if score >= 0.99 else "BLOCKED_EXACT",
        "metrics": {"audited_closure": score},
        "false_promotion": False,
        "replay_pass": True,
        "usage": usage,
        "public_result": {
            "case_id": request["case"]["case_id"],
            "seed": request["seed"],
            "statement": "deterministic protocol smoke result",
        },
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
