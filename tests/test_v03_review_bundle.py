from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matharc.v02.falsification import (
    KillTestKind,
    KillTestSpec,
    RouteEvaluationOutcome,
    RouteEvaluationRecord,
    attach_kill_test_spec,
    record_route_evaluation,
)
from matharc.v02.review_bundle import (
    AttackHistoryItem,
    Obligation,
    RequiredAssurance,
    ReviewBundle,
    ReviewBundleError,
    build_review_bundle,
    check_bundle_copy,
    check_obligation_copy,
    render_review_bundle_html,
    verify_review_bundle_files,
    write_review_bundle,
)
from matharc.v02.schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolCallRecord,
    ToolStatus,
)
from matharc.v02.trace import ResearchTrace


def _trace() -> ResearchTrace:
    trace = ResearchTrace(
        "V03-BUNDLE",
        TheoremContract(
            "K",
            "Prove C.",
            ("C",),
            "all symbolic inputs",
            assumptions=("standard arithmetic",),
            non_claims=("does not cover infinite precision",),
        ),
    )
    trace.add_claim(ClaimRecord("D", "base case holds", "n = 0", owner="p1"))
    trace.claims["D"].status = ClaimStatus.PROVED
    trace.add_claim(
        ClaimRecord("C", "n + 1 = 1 + n", "all integers n", dependencies=("D",), critical=True, owner="p1")
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
    trace.add_evidence(
        EvidenceRecord(
            evidence_id="EV-EXACT",
            claim_ids=("C",),
            kind=EvidenceKind.EXACT_COMPUTATION,
            status=EvidenceStatus.ACCEPTED,
            summary="direct computation",
            artifact_uri="mem://exact",
            digest_sha256="d" * 64,
            producer="prover-2",
            verifier="prover-2",
            independence_group="exact:1",
            replay_command="python replay.py",
            statement_correspondence="matches",
        )
    )
    trace.add_evidence(
        EvidenceRecord(
            evidence_id="EV-LIT",
            claim_ids=("C",),
            kind=EvidenceKind.LITERATURE_RESULT,
            status=EvidenceStatus.ACCEPTED,
            summary="cited from a paper",
            artifact_uri="mem://lit",
            digest_sha256="e" * 64,
            producer="literature-auditor-1",
            verifier="literature-auditor-1",
            independence_group="lit:1",
            statement_correspondence="matches the cited theorem",
        )
    )
    return trace


class BuildBundleTests(unittest.TestCase):
    def test_build_is_deterministic(self) -> None:
        # created_at is provenance-only and deliberately excluded from the
        # digest (matching KillTestSpec's convention), so two builds a few
        # microseconds apart legitimately differ there -- everything that
        # defines the bundle's actual content must not.
        trace = _trace()
        first = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        second = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        self.assertEqual(first.bundle_digest_sha256, second.bundle_digest_sha256)
        self.assertEqual(first.file_digests(), second.file_digests())
        first_payload = {k: v for k, v in first.to_dict().items() if k != "created_at"}
        second_payload = {k: v for k, v in second.to_dict().items() if k != "created_at"}
        self.assertEqual(first_payload, second_payload)

    def test_statement_correspondence_is_always_present_and_numbered(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        ids = [item.obligation_id for item in bundle.obligations]
        self.assertIn("OB-STATEMENT-CORRESPONDENCE", ids)

    def test_dependency_obligation_is_machine_sufficient(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        dep_obligations = [item for item in bundle.obligations if item.obligation_id == "OB-DEP-D"]
        self.assertEqual(len(dep_obligations), 1)
        self.assertEqual(dep_obligations[0].required_assurance, RequiredAssurance.MACHINE_SUFFICIENT)

    def test_non_machine_evidence_gets_a_human_obligation_exact_evidence_does_not(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        ids = {item.obligation_id for item in bundle.obligations}
        self.assertIn("OB-EVIDENCE-EV-LIT", ids)
        self.assertNotIn("OB-EVIDENCE-EV-EXACT", ids)

    def test_critical_claim_gets_independence_obligation_requiring_double_human_review(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        independence = [item for item in bundle.obligations if item.obligation_id == "OB-INDEPENDENCE"]
        self.assertEqual(len(independence), 1)
        self.assertEqual(independence[0].required_assurance, RequiredAssurance.HUMAN_DOUBLE)

    def test_dependency_path_contains_the_ancestor(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        dep_ids = [item["claim_id"] for item in bundle.dependency_path]
        self.assertEqual(dep_ids, ["D"])

    def test_pinned_definitions_come_from_the_contract(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        self.assertIn("standard arithmetic", bundle.pinned_definitions["assumptions"])
        self.assertIn("does not cover infinite precision", bundle.pinned_definitions["non_claims"])

    def test_unknown_claim_is_rejected(self) -> None:
        trace = _trace()
        with self.assertRaises(ReviewBundleError):
            build_review_bundle(trace, "NOPE", bundle_id="BUNDLE-1")

    def test_attack_history_round_trips(self) -> None:
        trace = _trace()
        attacks = (
            AttackHistoryItem("ATK-1", "tried n=0 edge case", emphasis=("edge case",)),
            AttackHistoryItem("ATK-2", "tried negative n"),
        )
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1", attack_history=attacks)
        restored = ReviewBundle.from_dict(bundle.to_dict())
        self.assertEqual(restored.attack_history, bundle.attack_history)

    def test_manually_built_bundle_without_statement_obligation_is_rejected(self) -> None:
        with self.assertRaises(ReviewBundleError):
            ReviewBundle(
                bundle_id="B",
                claim_id="C",
                claim_revision=0,
                statement="s",
                scope="scope",
                boundary="",
                pinned_definitions={},
                dependency_path=(),
                evidence=(),
                obligations=(),
                attack_history=(),
            )

    def test_from_dict_rejects_tampered_digest(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        payload = dict(bundle.to_dict())
        payload["bundle_digest_sha256"] = "0" * 64
        with self.assertRaises(ReviewBundleError):
            ReviewBundle.from_dict(payload)


class OnDiskIntegrityTests(unittest.TestCase):
    def test_write_then_verify_round_trips(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "bundle"
            write_review_bundle(bundle, out_dir)
            restored = verify_review_bundle_files(out_dir)
            self.assertEqual(restored.bundle_digest_sha256, bundle.bundle_digest_sha256)

    def test_tampering_any_file_is_detected(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "bundle"
            write_review_bundle(bundle, out_dir)
            (out_dir / "evidence.json").write_text('{"tampered": true}', encoding="utf-8")
            with self.assertRaises(ReviewBundleError):
                verify_review_bundle_files(out_dir)

    def test_tampering_the_manifest_itself_is_detected(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "bundle"
            write_review_bundle(bundle, out_dir)
            manifest_path = out_dir / "manifest.json"
            text = manifest_path.read_text(encoding="utf-8")
            manifest_path.write_text(text.replace(bundle.bundle_digest_sha256, "0" * 64), encoding="utf-8")
            with self.assertRaises(ReviewBundleError):
                verify_review_bundle_files(out_dir)

    def test_missing_bundle_file_is_detected(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "bundle"
            write_review_bundle(bundle, out_dir)
            (out_dir / "attacks.json").unlink()
            with self.assertRaises(ReviewBundleError):
                verify_review_bundle_files(out_dir)


class HtmlViewTests(unittest.TestCase):
    def test_renders_self_contained_html_with_no_raw_json_dump(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "bundle.html"
            written = render_review_bundle_html(bundle, out_path)
            text = written.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("<!doctype html>"))
        self.assertIn(bundle.claim_id, text)
        self.assertIn(bundle.bundle_digest_sha256, text)
        # A reviewer reading this page sees the obligation prose, not a
        # dump of the underlying dataclass field names.
        self.assertNotIn("required_assurance", text)
        self.assertNotIn("obligation_id", text)
        for item in bundle.obligations:
            self.assertIn(item.title, text)

    def test_html_escapes_untrusted_free_text_fields(self) -> None:
        trace = _trace()
        bundle = build_review_bundle(
            trace,
            "C",
            bundle_id="BUNDLE-1",
            attack_history=(AttackHistoryItem("ATK-1", "<script>alert(1)</script>"),),
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "bundle.html"
            written = render_review_bundle_html(bundle, out_path)
            text = written.read_text(encoding="utf-8")
        self.assertNotIn("<script>alert(1)</script>", text)
        self.assertIn("&lt;script&gt;", text)


class ObligationTests(unittest.TestCase):
    def test_obligation_requires_at_least_one_point(self) -> None:
        with self.assertRaises(ReviewBundleError):
            Obligation(
                obligation_id="OB-X",
                title="t",
                ask="a",
                points=(),
                ref="",
                required_assurance=RequiredAssurance.MACHINE_SUFFICIENT,
            )

    def test_generated_default_obligations_pass_the_copy_checker(self) -> None:
        # The real bug this test guards against: build_review_bundle's own
        # generator used to leak raw enum values (e.g. "LITERATURE_RESULT")
        # straight into obligation text, tripping the same checker it was
        # supposed to satisfy. Caught during self-review before this
        # shipped; kept as a permanent regression test.
        trace = _trace()
        bundle = build_review_bundle(trace, "C", bundle_id="BUNDLE-1")
        findings = check_bundle_copy(bundle)
        self.assertEqual(findings, {}, f"generated obligations are not clean: {findings}")


class CopyRuleRegressionTests(unittest.TestCase):
    """DEV_PATH_V03_DETAIL_V3.md appendix A's own before/after example,
    used as a literal regression fixture: the pre-revision text must be
    rejected and the post-revision text must pass."""

    def test_pre_revision_text_is_rejected(self) -> None:
        bad = Obligation(
            obligation_id="OB-REGRESSION",
            title="语句对应",
            ask=(
                '非正式语句与证书字段 new_residual（"Any q=6 outside-balance '
                'counterexample must have at least three small outside parts."）'
                "语义一致；「至少三个」与证书中排除 ≤2 的逻辑方向一致。"
            ),
            points=("见 ask",),
            ref="",
            required_assurance=RequiredAssurance.HUMAN_SINGLE,
        )
        violations = check_obligation_copy(bad)
        self.assertTrue(violations)
        joined = " ".join(violations)
        self.assertIn("new_residual", joined)

    def test_post_revision_text_passes(self) -> None:
        good = Obligation(
            obligation_id="OB-REGRESSION",
            title="白话与机器结论说的是同一件事吗",
            ask="上面那句白话，应当和机器算出的结论指同一件事。请确认转述方向没有说反。",
            points=(
                "机器给出的结论是：「小外部部件为 0、1、2 个的所有情形都已被排除」。"
                "白话说的「至少三个」与它等价——请确认这一步换算方向正确。",
                "机器只处理了 q=6 的情形，白话也必须限定在 q=6。",
            ),
            ref="证书的结论字段（原文为英文，可在证据区查看）",
            required_assurance=RequiredAssurance.HUMAN_SINGLE,
        )
        violations = check_obligation_copy(good)
        self.assertEqual(violations, ())

    def test_backend_enum_value_in_prose_is_rejected(self) -> None:
        obligation = Obligation(
            obligation_id="OB-X",
            title="check",
            ask="这条路线状态是 FALSIFIED，请确认。",
            points=("看状态即可。",),
            ref="",
            required_assurance=RequiredAssurance.MACHINE_SUFFICIENT,
        )
        violations = check_obligation_copy(obligation)
        self.assertTrue(any("FALSIFIED" in item for item in violations))

    def test_backend_field_name_in_prose_is_rejected(self) -> None:
        obligation = Obligation(
            obligation_id="OB-X",
            title="check",
            ask="请检查 independence_group 是否正确。",
            points=("看字段即可。",),
            ref="",
            required_assurance=RequiredAssurance.MACHINE_SUFFICIENT,
        )
        violations = check_obligation_copy(obligation)
        self.assertTrue(any("independence_group" in item for item in violations))

    def test_jargon_term_is_rejected(self) -> None:
        obligation = Obligation(
            obligation_id="OB-X",
            title="check",
            ask="这条路线的 kill test 是否合理？",
            points=("看测试即可。",),
            ref="",
            required_assurance=RequiredAssurance.MACHINE_SUFFICIENT,
        )
        violations = check_obligation_copy(obligation)
        self.assertTrue(any("kill test" in item for item in violations))

    def test_title_over_twenty_chars_is_rejected(self) -> None:
        obligation = Obligation(
            obligation_id="OB-X",
            title="这是一个故意写得非常非常非常长超过二十个字的标题用来测试规则",
            ask="随便",
            points=("随便",),
            ref="",
            required_assurance=RequiredAssurance.MACHINE_SUFFICIENT,
        )
        violations = check_obligation_copy(obligation)
        self.assertTrue(any("标题超过" in item for item in violations))

    def test_three_clauses_crammed_with_semicolons_is_rejected(self) -> None:
        obligation = Obligation(
            obligation_id="OB-X",
            title="check",
            ask="随便",
            points=("第一件事；第二件事；第三件事。",),
            ref="",
            required_assurance=RequiredAssurance.MACHINE_SUFFICIENT,
        )
        violations = check_obligation_copy(obligation)
        self.assertTrue(any("分号" in item for item in violations))


if __name__ == "__main__":
    unittest.main()
