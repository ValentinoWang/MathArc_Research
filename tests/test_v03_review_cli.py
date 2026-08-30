from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.cli import main
from matharc.v02.falsification import (
    KillTestKind,
    KillTestSpec,
    RouteEvaluationOutcome,
    RouteEvaluationRecord,
    attach_kill_test_spec,
    record_route_evaluation,
)
from matharc.v02.review import ObligationVerdict, ObligationVerdictKind, ReviewDecision, ReviewerProfile, ReviewRecord, statement_digest_sha256
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolCallRecord,
    ToolStatus,
)
from matharc.v02.trace import ResearchTrace, load_trace, save_trace

_REVIEWER_A = ReviewerProfile(
    reviewer_id="reviewer-A", name="A", affiliation="Uni A", independence_group="group-A"
)
_ROSTER_PAYLOAD = {
    "roster_version": "roster-1",
    "reviewers": [
        {
            "reviewer_id": "reviewer-A",
            "name": "A",
            "affiliation": "Uni A",
            "independence_group": "group-A",
            "conflict_of_interest_ids": [],
        }
    ],
}


def _candidate_trace_path(tmp_dir: Path) -> Path:
    trace = ResearchTrace(
        "V03-REVIEW-CLI",
        TheoremContract("K", "Prove C.", ("C",), "all symbolic inputs"),
    )
    trace.add_claim(
        ClaimRecord(
            "C", "n + 1 = 1 + n", "all integers n", status=ClaimStatus.CANDIDATE, owner="prover-1"
        )
    )
    trace.add_route(
        ResearchRoute(
            "R",
            "direct",
            "commute the addends",
            ("direct-computation",),
            "kill test",
            status=RouteStatus.ACTIVE,
            claim_ids=("C",),
            created_by="route-proposer",
        )
    )
    spec = KillTestSpec(
        kind=KillTestKind.ENUMERATION,
        generator_spec={"range": [0, 10]},
        discriminator_spec={"check": "commutativity"},
        tested_scope="n in [0, 10)",
    )
    attach_kill_test_spec(trace, "R", spec)
    trace.add_tool_call(
        ToolCallRecord(
            call_id="TC-1",
            tool="enumeration",
            purpose="check commutativity",
            status=ToolStatus.PASS,
            input_digest_sha256="a" * 64,
            output_digest_sha256="b" * 64,
            linked_claim_ids=("C",),
            independence_group="exact:1",
            replay_command="python -m matharc.v02 replay",
            started_at="2026-01-01T00:00:00Z",
            ended_at="2026-01-01T00:00:01Z",
        )
    )
    record_route_evaluation(
        trace,
        RouteEvaluationRecord(
            evaluation_id="EVAL-1",
            route_id="R",
            route_revision=0,
            claim_id="C",
            claim_revision=0,
            kill_test_spec_digest=spec.digest_sha256,
            tool_call_id="TC-1",
            outcome=RouteEvaluationOutcome.PASS_BOUNDED,
            tested_scope=spec.tested_scope,
            verifier_group="exact:1",
            replay_command="python -m matharc.v02 replay",
        ),
    )
    path = tmp_dir / "trace.json"
    save_trace(trace, path)
    return path


def _approve_record_payload(trace: ResearchTrace) -> dict[str, object]:
    claim = trace.claims["C"]
    record = ReviewRecord(
        review_id="REV-1",
        claim_id="C",
        claim_revision=claim.revision,
        statement_digest=statement_digest_sha256(claim.statement),
        bundle_digest="b" * 64,
        reviewer_id="reviewer-A",
        reviewer_profile_digest=_REVIEWER_A.digest_sha256,
        roster_version="roster-1",
        review_policy_version="policy-1",
        statement_correspondence="matches",
        verdicts=(ObligationVerdict("OB-STATEMENT-CORRESPONDENCE", ObligationVerdictKind.OK),),
        overall_decision=ReviewDecision.APPROVE,
    ).with_signature()
    return dict(record.to_dict())


class ColdFourStepFlowTests(unittest.TestCase):
    def test_nominate_bundle_submit_revoke_all_land_in_the_persisted_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            trace_path = _candidate_trace_path(tmp_dir)

            # Step 1: nominate -- a fresh `main()` call, nothing in memory
            # carried over from setup beyond the file on disk.
            nominate_output = tmp_dir / "nominate.json"
            main(
                [
                    "review",
                    "nominate",
                    "--trace",
                    str(trace_path),
                    "--claim",
                    "C",
                    "--output",
                    str(nominate_output),
                ]
            )
            nomination_result = json.loads(nominate_output.read_text(encoding="utf-8"))
            self.assertTrue(nomination_result["nominated"])

            # Step 2: bundle -- also a fresh main() call, reloading the
            # trace nominate just wrote back.
            bundle_dir = tmp_dir / "bundle"
            main(
                [
                    "review",
                    "bundle",
                    "--trace",
                    str(trace_path),
                    "--claim",
                    "C",
                    "--bundle-id",
                    "BUNDLE-1",
                    "--out-dir",
                    str(bundle_dir),
                ]
            )
            self.assertTrue((bundle_dir / "manifest.json").is_file())
            self.assertTrue((bundle_dir / "review.html").is_file())

            # Step 3: submit -- needs the roster installed first (via
            # --roster) and the record payload written by the reviewer's
            # own tooling.
            trace_after_bundle = load_trace(trace_path)
            record_path = tmp_dir / "review.json"
            record_path.write_text(
                json.dumps(_approve_record_payload(trace_after_bundle)), encoding="utf-8"
            )
            roster_path = tmp_dir / "roster.json"
            roster_path.write_text(json.dumps(_ROSTER_PAYLOAD), encoding="utf-8")
            submit_output = tmp_dir / "submit.json"
            main(
                [
                    "review",
                    "submit",
                    "--trace",
                    str(trace_path),
                    "--record",
                    str(record_path),
                    "--reviewer",
                    "reviewer-A",
                    "--roster",
                    str(roster_path),
                    "--output",
                    str(submit_output),
                ]
            )
            submit_result = json.loads(submit_output.read_text(encoding="utf-8"))
            self.assertTrue(submit_result["submitted"])
            self.assertEqual(submit_result["decision"], "APPROVE")
            evidence_id = submit_result["evidence_id"]

            trace_after_submit = load_trace(trace_path)
            self.assertIn(evidence_id, trace_after_submit.evidence)
            self.assertEqual(trace_after_submit.evidence[evidence_id].kind.value, "HUMAN_AUDIT")

            # Step 4: revoke -- fresh main() call again; the evidence
            # minted in step 3 must flip to STALE immediately.
            revoke_output = tmp_dir / "revoke.json"
            main(
                [
                    "review",
                    "revoke",
                    "--trace",
                    str(trace_path),
                    "--review-id",
                    "REV-1",
                    "--reason",
                    "conflict discovered after submission",
                    "--output",
                    str(revoke_output),
                ]
            )
            trace_after_revoke = load_trace(trace_path)
            self.assertEqual(trace_after_revoke.evidence[evidence_id].status.value, "STALE")

            # status reflects the whole cold chain.
            status_output = tmp_dir / "status.json"
            main(
                [
                    "review",
                    "status",
                    "--trace",
                    str(trace_path),
                    "--claim",
                    "C",
                    "--output",
                    str(status_output),
                ]
            )
            status_result = json.loads(status_output.read_text(encoding="utf-8"))
            self.assertEqual(len(status_result["nominations"]), 1)
            self.assertEqual(len(status_result["reviews"]), 1)
            self.assertEqual(status_result["reviews"][0]["lifecycle_status"], "REVOKED")


class CliRejectionTests(unittest.TestCase):
    def test_reviewer_outside_roster_is_rejected_with_nonzero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            trace_path = _candidate_trace_path(tmp_dir)
            main(["review", "nominate", "--trace", str(trace_path), "--claim", "C"])
            trace = load_trace(trace_path)
            payload = _approve_record_payload(trace)
            payload["reviewer_id"] = "ghost-reviewer"
            # Recompute the profile digest/signature so the record is
            # internally consistent up to the point where roster membership
            # (not record well-formedness) is what should fail.
            payload.pop("review_signature", None)  # stale; recomputed below for the new content
            record = ReviewRecord.from_dict({**payload, "reviewer_profile_digest": "f" * 64})
            record = record.with_signature()
            record_path = tmp_dir / "review.json"
            record_path.write_text(json.dumps(record.to_dict()), encoding="utf-8")
            roster_path = tmp_dir / "roster.json"
            roster_path.write_text(json.dumps(_ROSTER_PAYLOAD), encoding="utf-8")

            with self.assertRaises(SystemExit) as ctx:
                main(
                    [
                        "review",
                        "submit",
                        "--trace",
                        str(trace_path),
                        "--record",
                        str(record_path),
                        "--reviewer",
                        "ghost-reviewer",
                        "--roster",
                        str(roster_path),
                    ]
                )
            self.assertNotEqual(ctx.exception.code, 0)

    def test_conflicted_reviewer_is_rejected_with_nonzero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            trace_path = _candidate_trace_path(tmp_dir)
            main(["review", "nominate", "--trace", str(trace_path), "--claim", "C"])
            trace = load_trace(trace_path)

            conflicted_roster = {
                "roster_version": "roster-1",
                "reviewers": [
                    {
                        "reviewer_id": "reviewer-A",
                        "name": "A",
                        "affiliation": "",
                        "independence_group": "group-A",
                        "conflict_of_interest_ids": ["route-proposer"],
                    }
                ],
            }
            conflicted_profile = ReviewerProfile(
                reviewer_id="reviewer-A",
                name="A",
                affiliation="",
                independence_group="group-A",
                conflict_of_interest_ids=("route-proposer",),
            )
            payload = _approve_record_payload(trace)
            payload.pop("review_signature", None)  # stale; recomputed below for the new content
            record = ReviewRecord.from_dict(
                {**payload, "reviewer_profile_digest": conflicted_profile.digest_sha256}
            ).with_signature()
            record_path = tmp_dir / "review.json"
            record_path.write_text(json.dumps(record.to_dict()), encoding="utf-8")
            roster_path = tmp_dir / "roster.json"
            roster_path.write_text(json.dumps(conflicted_roster), encoding="utf-8")

            with self.assertRaises(SystemExit) as ctx:
                main(
                    [
                        "review",
                        "submit",
                        "--trace",
                        str(trace_path),
                        "--record",
                        str(record_path),
                        "--reviewer",
                        "reviewer-A",
                        "--roster",
                        str(roster_path),
                    ]
                )
            self.assertNotEqual(ctx.exception.code, 0)

    def test_nomination_of_a_non_candidate_claim_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            trace = ResearchTrace(
                "V03-REVIEW-CLI-2", TheoremContract("K", "p", ("C",), "s")
            )
            trace.add_claim(ClaimRecord("C", "stmt", "scope"))  # default OPEN, not CANDIDATE
            trace_path = tmp_dir / "trace.json"
            save_trace(trace, trace_path)
            with self.assertRaises(SystemExit) as ctx:
                main(["review", "nominate", "--trace", str(trace_path), "--claim", "C"])
            self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
