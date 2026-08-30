from __future__ import annotations

from pathlib import Path


FAKE_CODEX = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


args = sys.argv[1:]
if args == ["--version"]:
    print("codex-cli 0.0.fake")
    raise SystemExit(0)

log_path = os.environ.get("FAKE_CODEX_LOG", "")
if log_path:
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(args) + "\n")

prompt = sys.stdin.read()
delay = float(os.environ.get("FAKE_CODEX_SLEEP", "0"))
if delay:
    time.sleep(delay)

try:
    output_index = args.index("--output-last-message")
    output_path = Path(args[output_index + 1])
except (ValueError, IndexError):
    print("missing --output-last-message", file=sys.stderr)
    raise SystemExit(2)

thread_id = os.environ.get("FAKE_CODEX_THREAD", "thread-fake-001")
emit({"type": "thread.started", "thread_id": thread_id})
emit({"type": "turn.started"})
emit({
    "type": "item.completed",
    "item": {
        "id": "reason-1",
        "type": "reasoning",
        "text": "Freeze the selected obligation and try the cheapest falsifier first."
    }
})
emit({
    "type": "item.completed",
    "item": {
        "id": "todo-1",
        "type": "todo_list",
        "items": [
            {"text": "Inspect the frozen claim", "completed": True},
            {"text": "Design an exact replay", "completed": False}
        ]
    }
})
emit({
    "type": "item.completed",
    "item": {
        "id": "command-1",
        "type": "command_execution",
        "command": "python -m matharc validate --run artifacts/demo/run.json",
        "aggregated_output": "valid: true\n",
        "exit_code": 0,
        "status": "completed"
    }
})
emit({
    "type": "item.completed",
    "item": {
        "id": "message-1",
        "type": "agent_message",
        "text": "The selected claim remains proposal-only until verifier-matched evidence is attached."
    }
})
emit({
    "type": "turn.completed",
    "usage": {
        "input_tokens": 120,
        "cached_input_tokens": 0,
        "cache_write_input_tokens": 0,
        "output_tokens": 48,
        "reasoning_output_tokens": 16
    }
})

final = {
    "answer_markdown": "## Candidate next step\n\nRun an exact falsifier, then independently replay the surviving bridge.",
    "public_reasoning": {
        "objective": "Advance one selected load-bearing obligation.",
        "premises": ["The theorem contract and scope are frozen."],
        "plan": ["Attack the claim", "Design a replayable certificate"],
        "observations": ["The stored run is machine readable."],
        "falsification": ["Search the smallest boundary cases first."],
        "decision": "Keep the claim open pending exact evidence.",
        "uncertainty": "No independent certificate was produced in this fake turn."
    },
    "proposed_claims": [
        {
            "statement": "A candidate bridge should be checked independently.",
            "scope": "selected frozen scope",
            "confidence": 0.55,
            "verification_required": "exact certificate plus independent replay"
        }
    ],
    "suggested_tool_calls": [
        {
            "tool": "exact-checker",
            "purpose": "Try to falsify the bridge.",
            "arguments": {"mode": "smallest-counterexample"},
            "acceptance_rule": "A passing process alone is not proof; replay the certificate."
        }
    ],
    "claim_boundary": "No mathematical promotion occurred.",
    "next_actions": ["Create an exact artifact", "Attach it through ResearchEngine guards"]
}
output_path.write_text(json.dumps(final, ensure_ascii=False), encoding="utf-8")
'''


def write_fake_codex(directory: str | Path) -> Path:
    path = Path(directory) / "fake-codex"
    path.write_text(FAKE_CODEX, encoding="utf-8")
    path.chmod(0o755)
    return path
