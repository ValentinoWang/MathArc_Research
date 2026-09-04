"""Deterministic, credential-free end-to-end Agent loop demo.

The runner is intentionally a small adapter around the existing runtime
contracts.  It demonstrates the observable path
``question -> decomposition -> proposal -> exact tool -> independent replay``
without invoking Codex, a network, or a mathematical claim promotion API.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from ..schema import digest_json
from ..exact_tools import ExactToolResult, default_exact_tool_registry
from .synthesis import ExplorationCandidate, synthesize_candidate
from .verification import (
    ClaimBinding,
    VerificationStatus,
    bind_candidate_scope,
    convert_receipt_to_evidence,
    independent_replay,
)


DEFAULT_QUESTION = "Prove that the sum of the first n positive odd integers equals n squared."
DEMO_TIMESTAMP = "2000-01-01T00:00:00+00:00"
DEMO_WORKSPACE = "matharc-demo-workspace"


_CERTIFICATE = {
    "variable": "n",
    "base": {"at": 0, "lhs": "0", "rhs": "0*0"},
    "step": {
        "lhs": "(n*n) + (2*(n+1) - 1)",
        "rhs": "(n+1)*(n+1)",
    },
}


@dataclass(frozen=True, slots=True)
class DemoResult:
    """Stable public projection of one demo run."""

    question: str
    question_digest: str
    run_id: str
    status: str
    stages: Mapping[str, Any]
    provenance: Mapping[str, Any]
    evidence: Mapping[str, Any] | None = None
    output_paths: Mapping[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "matharc.runtime.agent-demo.v1",
            "question": self.question,
            "question_digest": self.question_digest,
            "run_id": self.run_id,
            "status": self.status,
            "stages": dict(self.stages),
            "provenance": dict(self.provenance),
            "evidence": dict(self.evidence) if self.evidence is not None else None,
            "output_paths": dict(self.output_paths or {}),
        }


def _is_odd_sum_question(question: str) -> bool:
    text = question.casefold()
    return (
        ("odd" in text or "奇数" in text)
        and ("square" in text or "squared" in text or "平方" in text or "n^2" in text)
    )


def _decompose(question: str, question_digest: str) -> dict[str, Any]:
    if not _is_odd_sum_question(question):
        return {
            "status": "BLOCKED",
            "reason": "No deterministic decomposition fixture matches this question.",
            "fixture": "odd-sum-induction-v1",
            "digest": digest_json({"status": "BLOCKED", "question_digest": question_digest}),
        }
    claims = (
        {
            "claim_id": "C-BASE",
            "statement": "The identity holds at n = 0.",
            "scope": "single base case",
            "dependencies": [],
        },
        {
            "claim_id": "C-STEP",
            "statement": "If the identity holds at n, then it holds at n + 1.",
            "scope": "every natural number n",
            "dependencies": ["C-BASE"],
        },
        {
            "claim_id": "C-TARGET",
            "statement": "For every n >= 0, 1 + 3 + ... + (2n - 1) = n^2.",
            "scope": "all natural numbers",
            "dependencies": ["C-BASE", "C-STEP"],
        },
    )
    result = {
        "status": "READY",
        "fixture": "odd-sum-induction-v1",
        "theorem": claims[-1]["statement"],
        "claims": list(claims),
        "route": {
            "route_id": "R-INDUCTION",
            "mechanism": ["mathematical induction", "symbolic polynomial normalization"],
        },
        "required_tools": ["induction_certificate"],
    }
    result["digest"] = digest_json(result)
    return result


def _proposal(decomposition: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic model-shaped proposal, without model access."""
    proposal = {
        "model": "deterministic-planner-v1",
        "acceptance_authority": False,
        "claim_boundary": "proposal and tool output never promote a theorem",
        "focus_claim_id": "C-STEP",
        "tool_request": {
            "template_id": "induction_certificate",
            "arguments": {"certificate": _CERTIFICATE},
        },
    }
    proposal["digest"] = digest_json({"decomposition_digest": decomposition["digest"], **proposal})
    return proposal


def _candidate(
    *, question_digest: str, run_id: str, decomposition: Mapping[str, Any], tool_result: ExactToolResult,
) -> tuple[ExplorationCandidate, ClaimBinding]:
    payload = {
        "proposition": "If the identity holds at n, then it holds at n + 1.",
        "quantifier": "for every natural number n",
        "objects": ["n"],
        "scope": "every natural number n",
        "template_id": "induction_certificate",
        "arguments": {"certificate": _CERTIFICATE},
    }
    candidate = synthesize_candidate(
        {
            "workspace_id": DEMO_WORKSPACE,
            "trace_id": f"trace-{question_digest[:16]}",
            "runtime_run_id": run_id,
            "generation_id": "generation-1",
            "worker_id": "deterministic-planner",
            "execution_id": "execution-tool-1",
        },
        task_digest=question_digest,
        source_digest=decomposition["digest"],
        evaluator_digest=digest_json({"evaluator": "induction-certificate"}),
        tool_registry_digest=digest_json(default_exact_tool_registry().template_ids()),
        budget_digest=digest_json({"max_steps": 1, "max_seconds": 1}),
        artifact_digest=tool_result.tool_call.output_digest_sha256,
        payload=payload,
        claim_ids=("C-STEP",),
    )
    binding = bind_candidate_scope(
        candidate,
        claim_id="C-STEP",
        proposition=payload["proposition"],
        quantifier=payload["quantifier"],
        objects=("n",),
        scope=payload["scope"],
    )
    return candidate, binding


def _stable_tool_record(result: ExactToolResult) -> dict[str, Any]:
    call = result.tool_call
    return {
        "tool": call.tool,
        "status": call.status.value,
        "input_digest_sha256": call.input_digest_sha256,
        "output_digest_sha256": call.output_digest_sha256,
        "independence_group": call.independence_group,
        "replay_command": call.replay_command,
        "environment_digest_sha256": call.environment_digest_sha256,
        "expected_discriminator": call.expected_discriminator,
    }


def _stable_candidate(candidate: ExplorationCandidate) -> dict[str, Any]:
    envelope = candidate.envelope.to_dict()
    return {
        "candidate_id": candidate.candidate_id,
        "identity_digest": candidate.envelope.identity_digest,
        "payload_digest": candidate.envelope.payload_digest,
        "artifact_digest": candidate.envelope.artifact_digest,
        "claim_ids": list(candidate.claim_ids),
        "provenance_digest": candidate.provenance_digest,
        "envelope": envelope,
    }


def run_agent_demo(question: str = DEFAULT_QUESTION, *, output_dir: str | Path | None = None) -> DemoResult:
    """Run the local demo and optionally write ``agent-demo.json/.md``."""
    question = str(question).strip()
    if not question:
        raise ValueError("question is required")
    question_digest = digest_json({"question": question})
    run_id = f"demo-{question_digest[:16]}"
    decomposition = _decompose(question, question_digest)
    stages: dict[str, Any] = {"decomposition": decomposition}
    provenance: dict[str, Any] = {
        "workspace_id": DEMO_WORKSPACE,
        "trace_id": f"trace-{question_digest[:16]}",
        "runtime_run_id": run_id,
        "generation_id": "generation-1",
        "network": False,
        "credentials": False,
        "deterministic": True,
    }
    if decomposition["status"] != "READY":
        result = DemoResult(question, question_digest, run_id, "BLOCKED", stages, provenance)
        return _write_result(result, output_dir)

    proposal = _proposal(decomposition)
    stages["proposal"] = proposal
    registry = default_exact_tool_registry()
    tool_result = registry.execute(
        "induction_certificate", claim_id="C-STEP", arguments={"certificate": _CERTIFICATE}
    )
    stages["tool"] = _stable_tool_record(tool_result)
    candidate, binding = _candidate(
        question_digest=question_digest,
        run_id=run_id,
        decomposition=decomposition,
        tool_result=tool_result,
    )
    stages["candidate"] = _stable_candidate(candidate)
    stages["claim_binding"] = binding.to_dict()

    def replay(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, Mapping) or payload.get("template_id") != "induction_certificate":
            return {"passed": False, "error": "unexpected candidate payload"}
        replay_result = registry.execute(
            str(payload["template_id"]),
            claim_id="C-STEP",
            arguments={"certificate": payload.get("arguments", {}).get("certificate", {})},
        )
        return {
            "passed": replay_result.tool_call.status.value == "PASS",
            "tool_output_digest": replay_result.tool_call.output_digest_sha256,
        }

    plan, receipt = independent_replay(
        candidate,
        verifier_id="deterministic-replay-verifier-v1",
        implementation_id="exact-tool:induction_certificate",
        replay=replay,
        environment={"mode": "clean", "network": False, "candidate_id": candidate.candidate_id},
    )
    receipt = replace(receipt, created_at=DEMO_TIMESTAMP)
    evidence = convert_receipt_to_evidence(
        candidate,
        receipt,
        artifact_uri="demo://agent-demo/induction-certificate",
        producer="deterministic-replay-verifier-v1",
        independence_group="deterministic-replay-verifier-v1",
    )
    stages["verification"] = {
        "status": receipt.status.value,
        "verifier_id": receipt.verifier_id,
        "implementation_id": plan.implementation_id,
        "replay_digest": plan.replay_digest,
        "result_digest": receipt.result_digest,
        "receipt_digest": receipt.receipt_digest,
        "receipt_binding_digest": receipt.receipt_binding_digest,
        "independent": receipt.independent,
    }
    stages["result"] = {
        "answer": "The odd-sum induction certificate passed independent replay.",
        "verified_claim_id": "C-STEP",
        "promotion_allowed": False,
        "boundary": "A verified step certificate is evidence, not automatic theorem promotion.",
    }
    evidence_dict = evidence.to_dict()
    evidence_dict["created_at"] = DEMO_TIMESTAMP
    return _write_result(
        DemoResult(
            question,
            question_digest,
            run_id,
            "VERIFIED_CERTIFICATE" if receipt.status is VerificationStatus.PASS else "BLOCKED",
            stages,
            provenance,
            evidence_dict,
        ),
        output_dir,
    )


def _markdown(result: DemoResult) -> str:
    payload = result.to_dict()
    decomposition = payload["stages"]["decomposition"]
    lines = [
        "# MathArc Agent Demo",
        "",
        f"- Status: `{result.status}`",
        f"- Question: {result.question}",
        f"- Question SHA-256: `{result.question_digest}`",
        f"- Runtime run: `{result.run_id}`",
        "",
        "## Observable Loop",
        "",
        f"1. Decomposition: `{decomposition['status']}` (`{decomposition['digest']}`)",
    ]
    if "proposal" in payload["stages"]:
        proposal = payload["stages"]["proposal"]
        tool = payload["stages"]["tool"]
        verification = payload["stages"]["verification"]
        final_result = payload["stages"]["result"]
        lines.extend(
            [
                f"2. Deterministic model proposal: `{proposal['digest']}`; authority `{proposal['acceptance_authority']}`",
                f"3. Exact tool: `{tool['tool']}` -> `{tool['status']}`; output `{tool['output_digest_sha256']}`",
                f"4. Independent replay: `{verification['status']}`; replay `{verification['replay_digest']}`",
                f"5. Evidence: `{payload['evidence']['evidence_id']}`; digest `{payload['evidence']['digest_sha256']}`",
                "",
                f"Result: {final_result['answer']} (claim `{final_result['verified_claim_id']}`)",
                "The certificate is verified, but this demo does not promote a theorem claim.",
            ]
        )
    else:
        lines.append(f"2. Tool/model execution: blocked (`{decomposition['reason']}`)")
    lines.extend(["", "## Provenance", "", "```json", json.dumps(payload["provenance"], indent=2), "```", ""])
    return "\n".join(lines)


def _write_result(result: DemoResult, output_dir: str | Path | None) -> DemoResult:
    if output_dir is None:
        return result
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "agent-demo.json"
    markdown_path = root / "agent-demo.md"
    payload = result.to_dict()
    payload["output_paths"] = {"json": str(json_path), "markdown": str(markdown_path)}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    updated = replace(result, output_paths=payload["output_paths"])
    markdown_path.write_text(_markdown(updated), encoding="utf-8")
    return updated


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic MathArc Agent loop demo")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--out-dir", default="artifacts/agent-demo")
    parser.add_argument("--json", action="store_true", help="print the full JSON result")
    args = parser.parse_args(argv)
    result = run_agent_demo(args.question, output_dir=args.out_dir)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) if args.json else _markdown(result))
    raise SystemExit(0 if result.status == "VERIFIED_CERTIFICATE" else 1)


if __name__ == "__main__":
    main()


__all__ = ["DEFAULT_QUESTION", "DemoResult", "run_agent_demo", "main"]
