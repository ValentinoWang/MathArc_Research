from __future__ import annotations

from pathlib import Path

FAKE_CLAUDE_CODE = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys


def emit(value):
    sys.stdout.write(json.dumps(value, ensure_ascii=False))
    sys.stdout.flush()


args = sys.argv[1:]

log_path = os.environ.get("FAKE_CLAUDE_LOG", "")
if log_path:
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(args) + "\n")

prompt = sys.stdin.read()

exit_code = int(os.environ.get("FAKE_CLAUDE_EXIT_CODE", "0"))
if exit_code != 0:
    print(os.environ.get("FAKE_CLAUDE_STDERR", "fake claude error"), file=sys.stderr)
    raise SystemExit(exit_code)

structured_raw = os.environ.get("FAKE_CLAUDE_STRUCTURED_OUTPUT", "")
if structured_raw:
    structured = json.loads(structured_raw)
else:
    structured = {
        "status": "progress",
        "executive_summary": "fake proposal",
        "public_reasoning": {
            "objective": "advance the focus claim",
            "premises": ["fake"],
            "proposed_move": "fake move",
            "observation": "fake observation",
            "falsification": "fake falsification",
            "decision": "candidate only",
        },
        "claim_boundary": "no promotion occurred",
    }

if os.environ.get("FAKE_CLAUDE_BAD_JSON") == "1":
    result_text = "not-json"
elif os.environ.get("FAKE_CLAUDE_OMIT_STRUCTURED") == "1":
    result_text = "I could not comply with the requested schema."
else:
    result_text = json.dumps(structured, ensure_ascii=False)

payload = {
    "type": "result",
    "subtype": "success",
    "is_error": os.environ.get("FAKE_CLAUDE_IS_ERROR") == "1",
    "session_id": os.environ.get("FAKE_CLAUDE_SESSION_ID", "fake-session-0001"),
    "duration_ms": 1,
    "total_cost_usd": float(os.environ.get("FAKE_CLAUDE_COST_USD", "0.01")),
    "usage": {
        "input_tokens": int(os.environ.get("FAKE_CLAUDE_INPUT_TOKENS", "100")),
        "output_tokens": int(os.environ.get("FAKE_CLAUDE_OUTPUT_TOKENS", "50")),
    },
    "result": result_text,
    "structured_output": structured if os.environ.get("FAKE_CLAUDE_OMIT_STRUCTURED") != "1" else None,
}
if os.environ.get("FAKE_CLAUDE_BAD_JSON") == "1":
    sys.stdout.write("not-json-at-all")
else:
    emit(payload)
'''


def write_fake_claude_code(directory: str | Path) -> Path:
    path = Path(directory) / "fake-claude"
    path.write_text(FAKE_CLAUDE_CODE, encoding="utf-8")
    path.chmod(0o755)
    return path
