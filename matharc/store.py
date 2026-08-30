from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import ResearchRun


def save_run(run: ResearchRun, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(run.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=target.name, dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def load_run(path: str | Path) -> ResearchRun:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return ResearchRun.from_dict(raw)
