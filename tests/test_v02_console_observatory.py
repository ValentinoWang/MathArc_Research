from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matharc.v02.budget import BudgetLedger
from matharc.v02.campaign import ResearchCampaign
from matharc.v02.falsification import (
    KillTestKind,
    KillTestSpec,
    RouteEvaluationOutcome,
    RouteEvaluationRecord,
    attach_kill_test_spec,
    record_route_evaluation,
)
from matharc.v02.review import (
    ObligationVerdict,
    ObligationVerdictKind,
    ReviewDecision,
    ReviewerProfile,
    ReviewerRoster,
    ReviewRecord,
    nominate_for_review,
    set_reviewer_roster,
    statement_digest_sha256,
)
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
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workers import StaticProposalWorker
from matharc.v02.workspace_server import make_server


_REVIEW_TOKEN = "same-origin-review-token-0123456789"
_REVIEWER = ReviewerProfile(
    reviewer_id="reviewer-A", name="A", affiliation="", independence_group="group-A"
)


def write_review_trace(path: Path) -> None:
    trace = ResearchTrace("SAME-ORIGIN-REVIEW", TheoremContract("K", "p", ("C",), "s"))
    trace.add_claim(
        ClaimRecord("C", "n + 1 = 1 + n", "all integers n", status=ClaimStatus.CANDIDATE, owner="p1")
    )
    trace.add_route(
        ResearchRoute(
            "R",
            "direct",
            "commute",
            ("m",),
            "kt",
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
            purpose="check",
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
    nominate_for_review(trace, "C")
    set_reviewer_roster(trace, ReviewerRoster(roster_version="roster-1", reviewers=(_REVIEWER,)))
    save_trace(trace, path)


class ConsoleObservatoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "workspace"
        write_full_workspace_bundle(self.root)
        self.console = self.root / "console.html"
        self.console.write_text("<!doctype html><title>Console fixture</title>", encoding="utf-8")
        self.server = make_server(self.root, host="127.0.0.1", port=0, dashboard_path=self.console)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2); self.temporary.cleanup()

    def test_missing_campaign_is_explicit_and_post_stays_read_only(self) -> None:
        with urlopen(self.base + "/api/campaign") as response:
            payload = json.loads(response.read().decode())
            self.assertFalse(payload["available"])
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        with self.assertRaises(HTTPError) as captured:
            urlopen(Request(self.base + "/api/campaign", data=b"{}", method="POST"))
        self.assertEqual(captured.exception.code, 405)

    def test_campaign_schema_and_console_dashboard_are_served(self) -> None:
        workspace = ResearchWorkspace.load(self.root)
        campaign = ResearchCampaign(
            workspace.trace,
            [StaticProposalWorker("prover", {})],
            budget=BudgetLedger(wall_seconds_limit=0.0),
        )
        workspace.record_campaign_result(campaign, campaign.run())
        workspace.save()
        with urlopen(self.base + "/api/campaign") as response:
            payload = json.loads(response.read().decode())
        self.assertTrue(payload["available"])
        self.assertEqual(
            payload["report"]["stop_reason"],
            "release_state_terminal:PROVED_AND_AUDITED",
        )
        with urlopen(self.base + "/") as response:
            self.assertIn("Console fixture", response.read().decode())

        with urlopen(self.base + "/api/console") as response:
            console = json.loads(response.read().decode())
        self.assertEqual(console["schema_version"], "1.0")
        self.assertTrue(console["workspace"]["audit"]["valid"])

    def test_missing_dashboard_is_not_generated_by_a_get_request(self) -> None:
        self.console.unlink()
        with self.assertRaises(HTTPError) as captured:
            urlopen(self.base + "/")
        self.assertEqual(captured.exception.code, 404)
        self.assertFalse(self.console.exists())

    def test_same_origin_review_requires_complete_opt_in_configuration(self) -> None:
        with self.assertRaisesRegex(ValueError, "supplied together"):
            make_server(
                self.root,
                host="127.0.0.1",
                port=0,
                dashboard_path=self.console,
                review_trace_path=self.root / "review-trace.json",
            )

    def test_same_origin_review_rejects_the_workspace_managed_trace(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not target"):
            make_server(
                self.root,
                host="127.0.0.1",
                port=0,
                dashboard_path=self.console,
                review_trace_path=self.root / "research-trace.json",
                review_write_token=_REVIEW_TOKEN,
            )

    def test_same_origin_review_rejects_a_symlink_to_the_managed_trace(self) -> None:
        alias = Path(self.temporary.name) / "managed-trace-alias.json"
        try:
            alias.symlink_to(self.root / "research-trace.json")
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        with self.assertRaisesRegex(ValueError, "must not target"):
            make_server(
                self.root,
                host="127.0.0.1",
                port=0,
                dashboard_path=self.console,
                review_trace_path=alias,
                review_write_token=_REVIEW_TOKEN,
            )


class SameOriginReviewAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "workspace"
        write_full_workspace_bundle(self.root)
        self.review_trace_path = Path(self.temporary.name) / "review-trace.json"
        write_review_trace(self.review_trace_path)
        dashboard = self.root / "console.html"
        dashboard.write_text("<!doctype html><title>Console fixture</title>", encoding="utf-8")
        self.server = make_server(
            self.root,
            host="127.0.0.1",
            port=0,
            dashboard_path=dashboard,
            review_trace_path=self.review_trace_path,
            review_write_token=_REVIEW_TOKEN,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2); self.temporary.cleanup()

    def _approve_payload(self) -> dict[str, object]:
        claim = load_trace(self.review_trace_path).claims["C"]
        return dict(
            ReviewRecord(
                review_id="REV-SAME-ORIGIN-1",
                claim_id="C",
                claim_revision=claim.revision,
                statement_digest=statement_digest_sha256(claim.statement),
                bundle_digest="b" * 64,
                reviewer_id=_REVIEWER.reviewer_id,
                reviewer_profile_digest=_REVIEWER.digest_sha256,
                roster_version="roster-1",
                review_policy_version="policy-1",
                statement_correspondence="matches",
                verdicts=(
                    ObligationVerdict("OB-STATEMENT-CORRESPONDENCE", ObligationVerdictKind.OK),
                ),
                overall_decision=ReviewDecision.APPROVE,
            ).with_signature().to_dict()
        )

    def test_same_origin_queue_bundle_and_post_use_the_existing_review_contract(self) -> None:
        with urlopen(self.base + "/api/review-queue") as response:
            queue = json.loads(response.read().decode("utf-8"))
        self.assertEqual(queue["queue"][0]["claim_id"], "C")
        self.assertFalse(queue["queue"][0]["has_active_review"])

        with urlopen(self.base + "/api/review-bundle/C") as response:
            bundle = json.loads(response.read().decode("utf-8"))
        self.assertEqual(bundle["claim_id"], "C")
        self.assertTrue(any(item["obligation_id"] == "OB-STATEMENT-CORRESPONDENCE" for item in bundle["obligations"]))

        body = json.dumps(self._approve_payload()).encode("utf-8")
        request = Request(
            self.base + "/api/review",
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {_REVIEW_TOKEN}", "Content-Type": "application/json"},
        )
        with urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))
        self.assertTrue(result["submitted"])
        self.assertIn(result["evidence_id"], load_trace(self.review_trace_path).evidence)

    def test_same_origin_rejects_missing_token_and_non_post_review_methods(self) -> None:
        request = Request(
            self.base + "/api/review",
            data=json.dumps(self._approve_payload()).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as captured:
            urlopen(request)
        self.assertEqual(captured.exception.code, 401)
        self.assertEqual(load_trace(self.review_trace_path).claims["C"].evidence_ids, ())

        with self.assertRaises(HTTPError) as captured:
            urlopen(Request(self.base + "/api/review-queue", method="PUT"))
        self.assertEqual(captured.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
