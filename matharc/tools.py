from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .hashing import digest_json, digest_text
from .models import ToolCallRecord, ToolStatus
from .polynomial import identity_certificate, parse_polynomial


@dataclass
class ToolExecution:
    call: ToolCallRecord
    output: dict[str, Any]


class PolynomialIdentityTool:
    name = "polynomial-identity-exact"

    def run(self, call_id: str, lhs: str, rhs: str, variable: str = "n") -> ToolExecution:
        started = time.perf_counter_ns()
        inputs = {"lhs": lhs, "rhs": rhs, "variable": variable}
        output = identity_certificate(lhs, rhs, variable)
        status = ToolStatus.PASS if output["valid"] else ToolStatus.COUNTEREXAMPLE
        duration = (time.perf_counter_ns() - started) // 1_000_000
        call = ToolCallRecord(
            call_id=call_id,
            tool_name=self.name,
            input_digest=digest_json(inputs),
            status=status,
            summary=("exact coefficient identity" if output["valid"] else "nonzero coefficient gap"),
            output_digest=digest_json(output),
            duration_ms=int(duration),
            replay_command=(
                "python -m matharc tool polynomial "
                f"--lhs {shlex.quote(lhs)} --rhs {shlex.quote(rhs)} --variable {shlex.quote(variable)}"
            ),
        )
        return ToolExecution(call=call, output=output)


class FiniteOddSumTool:
    name = "finite-odd-sum-checker"

    def run(self, call_id: str, maximum: int) -> ToolExecution:
        started = time.perf_counter_ns()
        if maximum < 0:
            raise ValueError("maximum must be nonnegative")
        failures = []
        for n in range(maximum + 1):
            lhs = sum(2 * k - 1 for k in range(1, n + 1))
            rhs = n * n
            if lhs != rhs:
                failures.append({"n": n, "lhs": lhs, "rhs": rhs})
        output = {
            "range": [0, maximum],
            "checked": maximum + 1,
            "failures": failures,
            "valid_on_finite_range": not failures,
            "scope_warning": "Finite checking does not prove the universal theorem.",
        }
        duration = (time.perf_counter_ns() - started) // 1_000_000
        call = ToolCallRecord(
            call_id=call_id,
            tool_name=self.name,
            input_digest=digest_json({"maximum": maximum}),
            status=ToolStatus.PASS if not failures else ToolStatus.COUNTEREXAMPLE,
            summary=f"checked n=0..{maximum}; failures={len(failures)}",
            output_digest=digest_json(output),
            duration_ms=int(duration),
            replay_command=f"python -m matharc tool finite-odd-sum --maximum {maximum}",
        )
        return ToolExecution(call=call, output=output)


class InductionCertificateTool:
    name = "induction-certificate-checker"

    def run(self, call_id: str, certificate: dict[str, Any]) -> ToolExecution:
        started = time.perf_counter_ns()
        variable = str(certificate.get("variable", "n"))
        base = certificate["base"]
        step = certificate["step"]
        base_n = int(base["at"])
        base_lhs = parse_polynomial(str(base["lhs"]), variable).evaluate(base_n)
        base_rhs = parse_polynomial(str(base["rhs"]), variable).evaluate(base_n)
        step_check = identity_certificate(str(step["lhs"]), str(step["rhs"]), variable)
        output = {
            "schema": "matharc.induction-certificate.v1",
            "variable": variable,
            "domain": certificate.get("domain", "natural numbers"),
            "base": {
                "at": base_n,
                "lhs_value": int(base_lhs),
                "rhs_value": int(base_rhs),
                "valid": base_lhs == base_rhs,
            },
            "step": step_check,
            "valid": base_lhs == base_rhs and step_check["valid"],
            "principle": "ordinary mathematical induction on natural numbers",
        }
        duration = (time.perf_counter_ns() - started) // 1_000_000
        status = ToolStatus.PASS if output["valid"] else ToolStatus.FAIL
        replay_payload = json.dumps(certificate, ensure_ascii=False, sort_keys=True)
        call = ToolCallRecord(
            call_id=call_id,
            tool_name=self.name,
            input_digest=digest_json(certificate),
            status=status,
            summary=("base and symbolic induction step verified" if output["valid"] else "invalid induction certificate"),
            output_digest=digest_json(output),
            duration_ms=int(duration),
            replay_command=(
                "python -m matharc tool induction --certificate-json "
                + shlex.quote(replay_payload)
            ),
        )
        return ToolExecution(call=call, output=output)


class LeanTool:
    name = "lean-kernel"

    def run(
        self,
        call_id: str,
        source: str,
        command: str | None = None,
        timeout_seconds: int = 60,
    ) -> ToolExecution:
        started = time.perf_counter_ns()
        command = command or os.environ.get("MATHARC_LEAN_COMMAND", "lake env lean")
        with tempfile.TemporaryDirectory(prefix="matharc-lean-") as directory:
            path = Path(directory) / "Main.lean"
            path.write_text(source, encoding="utf-8")
            try:
                completed = subprocess.run(
                    [*shlex.split(command), str(path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
                output = {
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "source_sha256": digest_text(source),
                }
                status = ToolStatus.PASS if completed.returncode == 0 else ToolStatus.FAIL
            except FileNotFoundError as exc:
                output = {"error": str(exc), "source_sha256": digest_text(source)}
                status = ToolStatus.ERROR
            except subprocess.TimeoutExpired as exc:
                output = {"error": str(exc), "source_sha256": digest_text(source)}
                status = ToolStatus.TIMEOUT
        duration = (time.perf_counter_ns() - started) // 1_000_000
        call = ToolCallRecord(
            call_id=call_id,
            tool_name=self.name,
            input_digest=digest_json({"source_sha256": digest_text(source), "command": command}),
            status=status,
            summary=f"Lean kernel status={status.value}",
            output_digest=digest_json(output),
            duration_ms=int(duration),
            replay_command=f"{command} Main.lean",
        )
        return ToolExecution(call=call, output=output)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Any] = {
            "polynomial": PolynomialIdentityTool(),
            "finite-odd-sum": FiniteOddSumTool(),
            "induction": InductionCertificateTool(),
            "lean": LeanTool(),
        }

    def get(self, name: str) -> Any:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"unknown tool {name!r}; available={sorted(self._tools)}") from exc
