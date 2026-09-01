from __future__ import annotations

import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from matharc.v02.falsification import (
    KillTestKind,
    KillTestSpec,
    RouteEvaluationOutcome,
    RouteEvaluationRecord,
    attach_kill_test_spec,
    record_route_evaluation,
)
from matharc.v02.review import ObligationVerdict, ObligationVerdictKind, ReviewDecision, ReviewerProfile, ReviewerRoster, ReviewRecord, nominate_for_review, reviews_for_claim, set_reviewer_roster, statement_digest_sha256
from matharc.v02.review_server import ReviewServerError, make_review_server
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

_TOKEN = "test-secret-token-0123456789"
_REVIEWER_A = ReviewerProfile(
    reviewer_id="reviewer-A", name="A", affiliation="", independence_group="group-A"
)
_REVIEWER_B = ReviewerProfile(
    reviewer_id="reviewer-B", name="B", affiliation="", independence_group="group-B"
)


class ReviewServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.trace_path = Path(self.temporary.name) / "trace.json"
        trace = ResearchTrace("V03-SERVER", TheoremContract("K", "p", ("C",), "s"))
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
        set_reviewer_roster(trace, ReviewerRoster(roster_version="roster-1", reviewers=(_REVIEWER_A, _REVIEWER_B)))
        save_trace(trace, self.trace_path)

        self.server = make_review_server(self.trace_path, write_token=_TOKEN, host="127.0.0.1", port=0)
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        )
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def get_json(self, path: str) -> dict[str, object]:
        with urlopen(self.base + path, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return dict(json.loads(response.read().decode("utf-8")))

    def _approve_payload(
        self, review_id: str = "REV-1", reviewer: ReviewerProfile = _REVIEWER_A
    ) -> dict[str, object]:
        trace = load_trace(self.trace_path)
        claim = trace.claims["C"]
        record = ReviewRecord(
            review_id=review_id,
            claim_id="C",
            claim_revision=claim.revision,
            statement_digest=statement_digest_sha256(claim.statement),
            bundle_digest="b" * 64,
            reviewer_id=reviewer.reviewer_id,
            reviewer_profile_digest=reviewer.digest_sha256,
            roster_version="roster-1",
            review_policy_version="policy-1",
            statement_correspondence="matches",
            verdicts=(ObligationVerdict("OB-STATEMENT-CORRESPONDENCE", ObligationVerdictKind.OK),),
            overall_decision=ReviewDecision.APPROVE,
        ).with_signature()
        return dict(record.to_dict())

    def test_review_queue_shows_the_nomination(self) -> None:
        queue = self.get_json("/api/review-queue")
        rows = queue["queue"]
        assert isinstance(rows, list)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["claim_id"], "C")
        self.assertFalse(rows[0]["has_active_review"])

    def test_review_bundle_view_model_has_no_unmapped_backend_tokens(self) -> None:
        payload = self.get_json("/api/review-bundle/C")
        text = json.dumps(payload, ensure_ascii=False)
        # Negative test: none of these raw backend enum values may leak
        # into the response text.
        for forbidden in ("CANDIDATE", "ACTIVE", "PASS_BOUNDED", "MACHINE_SUFFICIENT"):
            self.assertNotIn(forbidden, text)
        self.assertEqual(payload["claim_id"], "C")
        obligations = payload["obligations"]
        assert isinstance(obligations, list)
        self.assertTrue(any(item["obligation_id"] == "OB-STATEMENT-CORRESPONDENCE" for item in obligations))

    def test_review_bundle_for_unknown_claim_is_404(self) -> None:
        with self.assertRaises(HTTPError) as ctx:
            self.get_json("/api/review-bundle/NOPE")
        self.assertEqual(ctx.exception.code, 404)

    def test_post_without_token_is_unauthorized_and_does_not_mutate(self) -> None:
        body = json.dumps(self._approve_payload()).encode("utf-8")
        request = Request(
            self.base + "/api/review", data=body, method="POST", headers={"Content-Type": "application/json"}
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=5)
        self.assertEqual(ctx.exception.code, 401)
        trace_after = load_trace(self.trace_path)
        self.assertEqual(trace_after.claims["C"].evidence_ids, ())

    def test_post_with_wrong_token_is_unauthorized(self) -> None:
        body = json.dumps(self._approve_payload()).encode("utf-8")
        request = Request(
            self.base + "/api/review",
            data=body,
            method="POST",
            headers={"Authorization": "Bearer wrong-token", "Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=5)
        self.assertEqual(ctx.exception.code, 401)

    def test_post_with_correct_token_submits_and_mints_evidence(self) -> None:
        body = json.dumps(self._approve_payload()).encode("utf-8")
        request = Request(
            self.base + "/api/review",
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {_TOKEN}", "Content-Type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
            result = json.loads(response.read().decode("utf-8"))
        self.assertTrue(result["submitted"])
        self.assertEqual(result["decision"], "APPROVE")
        evidence_id = result["evidence_id"]
        trace_after = load_trace(self.trace_path)
        self.assertIn(evidence_id, trace_after.evidence)
        self.assertEqual(trace_after.evidence[evidence_id].kind.value, "HUMAN_AUDIT")

    def test_concurrent_posts_through_two_servers_preserve_both_reviews(self) -> None:
        other = make_review_server(self.trace_path, write_token=_TOKEN, host="127.0.0.1", port=0)
        other_thread = threading.Thread(target=other.serve_forever, daemon=True)
        other_thread.start()
        other_base = f"http://127.0.0.1:{other.server_address[1]}"
        barrier = threading.Barrier(2)

        def post(base: str, payload: dict[str, object]) -> dict[str, object]:
            barrier.wait(timeout=5)
            request = Request(
                base + "/api/review",
                data=json.dumps(payload).encode("utf-8"),
                method="POST",
                headers={"Authorization": f"Bearer {_TOKEN}", "Content-Type": "application/json"},
            )
            with urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 200)
                return dict(json.loads(response.read().decode("utf-8")))

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(post, self.base, self._approve_payload("REV-CONCURRENT-A", _REVIEWER_A))
                second = pool.submit(post, other_base, self._approve_payload("REV-CONCURRENT-B", _REVIEWER_B))
                results = [first.result(timeout=10), second.result(timeout=10)]
        finally:
            other.shutdown(); other.server_close(); other_thread.join(timeout=2)

        self.assertEqual({item["review_id"] for item in results}, {"REV-CONCURRENT-A", "REV-CONCURRENT-B"})
        trace_after = load_trace(self.trace_path)
        self.assertEqual(
            {item.review_id for item in reviews_for_claim(trace_after, "C")},
            {"REV-CONCURRENT-A", "REV-CONCURRENT-B"},
        )
        self.assertEqual(
            set(trace_after.evidence),
            {"EV-REVIEW-REV-CONCURRENT-A", "EV-REVIEW-REV-CONCURRENT-B"},
        )

    def test_post_body_over_64kb_is_rejected(self) -> None:
        oversized = json.dumps({"padding": "x" * (70 * 1024)}).encode("utf-8")
        request = Request(
            self.base + "/api/review",
            data=oversized,
            method="POST",
            headers={"Authorization": f"Bearer {_TOKEN}", "Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=5)
        self.assertEqual(ctx.exception.code, 413)

    def test_get_on_the_write_endpoint_is_405(self) -> None:
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self.base + "/api/review", timeout=5)
        self.assertEqual(ctx.exception.code, 405)

    def test_put_anywhere_is_405(self) -> None:
        request = Request(self.base + "/api/review-queue", method="PUT")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=5)
        self.assertEqual(ctx.exception.code, 405)


class ReviewServerConfigTests(unittest.TestCase):
    def test_short_or_default_token_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace_path = Path(tmp) / "trace.json"
            trace = ResearchTrace("T", TheoremContract("K", "p", ("C",), "s"))
            trace.add_claim(ClaimRecord("C", "stmt", "scope"))
            save_trace(trace, trace_path)
            with self.assertRaises(ReviewServerError):
                make_review_server(trace_path, write_token="short", port=0)


if __name__ == "__main__":
    unittest.main()
