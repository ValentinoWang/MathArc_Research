"""Offline, source-pinned execution of the three T2 dogfood archives."""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from typing import Any, Mapping
from .budget import BudgetLedger
from .novelty_audit import CandidateResult, NoveltyAuditPurpose, NoveltyAuditRecord, NoveltyConclusion, SearchRoute, SearchRouteResult, SourceSupport
from .problem_status import ObservationDigestRef, OpenStatusCertificate, ProblemDossierSnapshot, ProblemStatus, StatementVersion
from .schema import canonical_json, digest_json
from .source_observation import LicenseStatus, SourceObservation
from .topic_observation import ManualReviewReason, TopicObservationBatch, TopicObservationInput, TopicObservationRunner, TopicRunStatus

_SCHEMA_VERSION = "1.1"
_TOPIC_ID = "union-closed"
_S1_NAMES = ("frankl-q6.json", "resolved-collision.json", "confirmed-open.json")
_CASE_ORDER = ("P-FRANKL-Q6", "P-ARXIV-2601-22401-COLLISION", "P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS")
_ROLES = {"P-FRANKL-Q6": "frankl-q6-constrained-residual", "P-ARXIV-2601-22401-COLLISION": "database-open-literature-resolved-collision", "P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS": "frankl-q6-four-or-more-small-outside-parts-residual"}

class DogfoodArchiveError(ValueError):
    """Raised when a fixture, source artifact, or persisted archive is invalid."""

def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise DogfoodArchiveError(f"{field} must be non-empty")
    return value

def _fields(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    unknown, missing = set(value) - expected, expected - set(value)
    if unknown: raise DogfoodArchiveError(f"unknown {name} fields: {sorted(unknown)}")
    if missing: raise DogfoodArchiveError(f"missing {name} fields: {sorted(missing)}")

class DogfoodArchiveRunner:
    """Run and replay exactly three checked-in, provenance-bound archives."""
    def __init__(self, root: str | Path, fixture_root: str | Path) -> None:
        self.root, self.fixture_root = Path(root), Path(fixture_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.contract_path = self.fixture_root / "three-real-archives.json"
        if not self.contract_path.exists(): self.contract_path = self.fixture_root.parent / "t2-fixtures" / "three-real-archives.json"
        self.result_path, self.contract = self.root / "dogfood-archives.json", {}

    def run(self) -> dict[str, Any]:
        self.contract = self._load_contract()
        fixtures = self._load_s1_fixtures()
        specs = self._load_source_specs()
        if self.result_path.exists(): return self._replay(specs)
        return self._execute(fixtures, specs)

    def _load_contract(self) -> dict[str, Any]:
        try: contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise DogfoodArchiveError("T2 contract is unreadable") from exc
        if not isinstance(contract, dict): raise DogfoodArchiveError("T2 contract must be an object")
        _fields(contract, {"fixture_kind", "topic_id", "source_fixture_directory", "fixture_sha256", "source_artifacts", "expected_budget_snapshot", "expected_budget_digest_sha256", "non_claim_boundary", "cases"}, "T2 contract")
        if contract["fixture_kind"] != "t2-dogfood-archive-contract" or contract["topic_id"] != _TOPIC_ID: raise DogfoodArchiveError("incompatible T2 contract identity")
        if not isinstance(contract["cases"], list) or len(contract["cases"]) != 3: raise DogfoodArchiveError("T2 contract must define exactly three cases")
        case_fields = {"problem_id", "case_role", "expected_topic_status", "expected_problem_status", "expected_manual_reason", "expected_novelty_status", "expected_promotion_allowed"}
        ids = []
        for case in contract["cases"]:
            if not isinstance(case, dict): raise DogfoodArchiveError("T2 contract case must be an object")
            _fields(case, case_fields, "T2 contract case")
            problem_id = _text(case["problem_id"], "contract problem_id")
            if problem_id not in _ROLES or case["case_role"] != _ROLES[problem_id]: raise DogfoodArchiveError("unknown or mismatched contract case")
            if case["expected_promotion_allowed"] is not False: raise DogfoodArchiveError("dogfood promotion must remain disabled")
            ids.append(problem_id)
        if tuple(ids) != _CASE_ORDER: raise DogfoodArchiveError("contract case order or identity drift")
        if set(contract["fixture_sha256"]) != set(_S1_NAMES) or any(not isinstance(value, str) or len(value) != 64 for value in contract["fixture_sha256"].values()):
            raise DogfoodArchiveError("fixture_sha256 must cover exactly the three S1 fixtures")
        if contract["expected_budget_snapshot"] != self._new_residual_budget().to_dict():
            raise DogfoodArchiveError("T2 contract budget identity is incompatible")
        if contract["expected_budget_digest_sha256"] != digest_json(contract["expected_budget_snapshot"]):
            raise DogfoodArchiveError("T2 contract budget digest mismatch")
        if not isinstance(contract["source_artifacts"], dict): raise DogfoodArchiveError("source_artifacts must be an object")
        return contract

    @staticmethod
    def _new_residual_budget() -> BudgetLedger:
        budget = BudgetLedger(input_token_limit=1)
        budget.charge_model_usage({"input_tokens": 1})
        return budget

    def _load_s1_fixtures(self) -> dict[str, dict[str, Any]]:
        paths = sorted(self.fixture_root.glob("*.json"))
        if tuple(path.name for path in paths) != tuple(sorted(_S1_NAMES)): raise DogfoodArchiveError("S1 fixture directory must contain exactly the three named fixtures")
        values = {}
        for path in paths:
            expected_sha = self.contract["fixture_sha256"].get(path.name)
            actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            if expected_sha != actual_sha: raise DogfoodArchiveError(f"S1 fixture digest mismatch: {path.name}")
            try: payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc: raise DogfoodArchiveError(f"fixture is unreadable: {path.name}") from exc
            if not isinstance(payload, dict): raise DogfoodArchiveError(f"fixture must be an object: {path.name}")
            problem_id = _text(payload.get("problem_id"), "problem_id")
            if problem_id not in _ROLES or payload.get("case_role") != _ROLES[problem_id]: raise DogfoodArchiveError("unknown or mismatched S1 case")
            for field in ("statement", "source_assertions", "expected_report_status", "limitations"):
                if field not in payload: raise DogfoodArchiveError(f"missing S1 fixture field: {field}")
            if not isinstance(payload["source_assertions"], list) or not payload["source_assertions"]:
                raise DogfoodArchiveError("missing source assertions")
            for assertion in payload["source_assertions"]:
                if not isinstance(assertion, dict): raise DogfoodArchiveError("malformed source assertion")
                required = {"source_kind", "assertion"} | ({"source_path"} if problem_id != _CASE_ORDER[1] else set())
                if problem_id == _CASE_ORDER[1]:
                    if not required.issubset(assertion): raise DogfoodArchiveError("missing S1 source assertion fields")
                else:
                    _fields(assertion, required, "S1 source assertion")
            if problem_id == _CASE_ORDER[1]:
                chain = payload.get("source_chain")
                if not isinstance(chain, list) or not chain: raise DogfoodArchiveError("missing collision source_chain")
                for entry in chain: _fields(entry, {"source_kind", "canonical_uri", "pinned_version", "locator", "assertion"}, "collision source provenance")
            values[problem_id] = payload
        if set(values) != set(_CASE_ORDER): raise DogfoodArchiveError("S1 fixtures do not define exactly three cases")
        return {key: values[key] for key in _CASE_ORDER}

    def _load_source_specs(self) -> dict[str, list[dict[str, str]]]:
        raw, specs = self.contract["source_artifacts"], {}
        required = {"path", "sha256", "canonical_uri", "pinned_version", "locator"}
        for problem_id in _CASE_ORDER:
            if problem_id not in raw: raise DogfoodArchiveError(f"missing source_artifacts for {problem_id}")
            entries = raw[problem_id] if isinstance(raw[problem_id], list) else [raw[problem_id]]
            specs[problem_id] = []
            for item in entries:
                if not isinstance(item, dict): raise DogfoodArchiveError("source artifact spec must be an object")
                _fields(item, required | ({"source_kind", "reported_status"} if problem_id == _CASE_ORDER[1] else set()), "source artifact spec")
                path = self.contract_path.parent / item["path"]
                if not path.is_file(): raise DogfoodArchiveError(f"missing source artifact: {item['path']}")
                content = path.read_bytes()
                if hashlib.sha256(content).hexdigest() != item["sha256"]: raise DogfoodArchiveError(f"source artifact digest mismatch: {item['path']}")
                for field in required: _text(item[field], field)
                specs[problem_id].append(dict(item))
        return specs

    def _inputs_for(self, fixture: Mapping[str, Any], specs: list[dict[str, str]]) -> tuple[tuple[TopicObservationInput, ...], list[dict[str, str]]]:
        inputs, provenance = [], []
        for index, spec in enumerate(specs):
            path, content = self.contract_path.parent / spec["path"], (self.contract_path.parent / spec["path"]).read_bytes()
            source_id = "source-" + hashlib.sha256(f"{spec['canonical_uri']}|{spec['pinned_version']}".encode()).hexdigest()[:24]
            observation = SourceObservation(source_id, spec["canonical_uri"], spec["pinned_version"], "2026-08-31T11:00:00+00:00", LicenseStatus.OPEN, "Checked-in pinned artifact license/provenance record.", f"Pinned source artifact for {fixture['case_role']}.", "T2 source artifact contract.", "text/html" if path.suffix == ".html" else "text/plain", hashlib.sha256(content).hexdigest())
            inputs.append(TopicObservationInput(f"{fixture['problem_id']}:source:{index:02d}", observation, content))
            provenance.append({"source_id": source_id, "source_kind": spec.get("source_kind", "local-document"), "canonical_uri": spec["canonical_uri"], "pinned_version": spec["pinned_version"], "locator": spec["locator"], "artifact_path": spec["path"], "content_sha256": observation.content_digest_sha256, **({"reported_status": spec["reported_status"]} if "reported_status" in spec else {})})
        return tuple(inputs), provenance

    def _execute(self, fixtures: Mapping[str, Mapping[str, Any]], specs: Mapping[str, list[dict[str, str]]]) -> dict[str, Any]:
        main = TopicObservationRunner(self.root / "topic-observation", topic_id=_TOPIC_ID, initial_cursor="dogfood-c0")
        fi, fp = self._inputs_for(fixtures[_CASE_ORDER[0]], specs[_CASE_ORDER[0]])
        first, replay = main.run(TopicObservationBatch(_TOPIC_ID, "dogfood-c0", "dogfood-c1", fi)), main.run(TopicObservationBatch(_TOPIC_ID, "dogfood-c0", "dogfood-c1", fi))
        if first.status is not TopicRunStatus.APPLIED or replay.status is not TopicRunStatus.REPLAYED: raise DogfoodArchiveError("Frankl cursor replay failed")
        ci, cp = self._inputs_for(fixtures[_CASE_ORDER[1]], specs[_CASE_ORDER[1]])
        cr = main.run(TopicObservationBatch(_TOPIC_ID, "dogfood-c1", "dogfood-c2", ci))
        if cr.status is not TopicRunStatus.APPLIED: raise DogfoodArchiveError("collision source import failed")
        observations = {item.observation_id: item for item in main.literature.observations}
        cs = self._reported_status(fixtures[_CASE_ORDER[0]], fp, observations, main), self._reported_status(fixtures[_CASE_ORDER[1]], cp, observations, main)
        alert = TopicObservationInput("collision-review-alert", ci[0].observation, ci[0].content, ("reported-resolution",))
        ar = main.run(TopicObservationBatch(_TOPIC_ID, "dogfood-c2", "dogfood-c3", (alert,)))
        duplicate = TopicObservationInput("collision-review-recheck", ci[0].observation, ci[0].content)
        dr = main.run(TopicObservationBatch(_TOPIC_ID, "dogfood-c3", "dogfood-c4", (duplicate,)))
        if ar.status is not TopicRunStatus.MANUAL_REVIEW or dr.item_results[0].status.value != "DUPLICATE": raise DogfoodArchiveError("collision review/replay boundary failed")
        ri, rp = self._inputs_for(fixtures[_CASE_ORDER[2]], specs[_CASE_ORDER[2]])
        budget = self._new_residual_budget()
        residual_runner = TopicObservationRunner(self.root / "residual-budget", topic_id=_TOPIC_ID, initial_cursor="budget-c0", budget=budget)
        rr = residual_runner.run(TopicObservationBatch(_TOPIC_ID, "budget-c0", "budget-c1", ri))
        if rr.status is not TopicRunStatus.MANUAL_REVIEW: raise DogfoodArchiveError("residual budget boundary failed")
        rs = self._insufficient_status(fixtures[_CASE_ORDER[2]], ri[0].observation, residual_runner)
        blocking = sorted(item.manual_id for item in (*main.manual_queue, *residual_runner.manual_queue))
        budget_snapshot = budget.to_dict()
        if budget_snapshot != self.contract["expected_budget_snapshot"]:
            raise DogfoodArchiveError("executed residual budget does not match T2 contract")
        result = {"schema_version": _SCHEMA_VERSION, "topic_id": _TOPIC_ID, "contract_digest_sha256": self._contract_digest(), "fixture_identity_digest_sha256": digest_json(self.contract["fixture_sha256"]), "source_identity_digest_sha256": digest_json(specs), "fixture_files": list(_S1_NAMES), "replayed": False, "archive_blocked": bool(blocking), "blocking_manual_ids": blocking, "cases": [self._case(fixtures[_CASE_ORDER[0]], fp, first.status.value, replay.status.value, cs[0], "LIMITED_REPORTED_OPEN_NO_PROMOTION"), self._case(fixtures[_CASE_ORDER[1]], cp, cr.status.value, dr.item_results[0].status.value, cs[1], "REPORTED_RESOLUTION_REQUIRES_INDEPENDENT_MATHEMATICAL_REVIEW", ManualReviewReason.HIGH_RISK_EVENT.value, self._collision_audit(fixtures[_CASE_ORDER[1]], cp, observations, main)), self._case(fixtures[_CASE_ORDER[2]], rp, rr.status.value, "NOT_APPLICABLE", rs, "REPORTED_OPEN_EVIDENCE_INSUFFICIENT_NO_PROMOTION", ManualReviewReason.BUDGET_EXHAUSTED.value)], "budget_snapshot": budget_snapshot, "budget_digest_sha256": digest_json(budget_snapshot), "no_claim_or_trace_created": self._no_claim_or_trace_created()}
        if not result["archive_blocked"] or not result["no_claim_or_trace_created"]: raise DogfoodArchiveError("dogfood archive boundary failed")
        self._assert_contract_results(result)
        self._save(result); return result

    def _reported_status(self, fixture, provenance, observations, runner):
        statement = StatementVersion(fixture["problem_id"], fixture["statement_version"], fixture["statement"])
        cert = OpenStatusCertificate(f"status-{fixture['problem_id']}", fixture["problem_id"], fixture["statement_version"], statement.statement_version_id, statement.statement_digest_sha256, tuple(ObservationDigestRef.from_observation(observations[key]) for key in sorted({p["source_id"] for p in provenance})), ProblemStatus(fixture["expected_report_status"]), tuple(fixture["limitations"]), "dogfood-status-reporter", "2026-08-31T11:15:00+00:00", "2026-09-30T00:00:00+00:00")
        dossier = ProblemDossierSnapshot(f"dossier-{fixture['problem_id']}", fixture["problem_id"], fixture["statement_version"], statement, cert, "2026-08-31T11:20:00+00:00")
        validation = dossier.validate(observations, as_of="2026-08-31T12:00:00+00:00", artifacts=runner.literature.artifacts)
        if validation.status is not cert.status: raise DogfoodArchiveError("source readback status mismatch")
        return {"reported_status": cert.status.value, "validated_status": validation.status.value, "invalidations": [x.value for x in validation.invalidations], "dossier": dossier.to_dict()}

    def _insufficient_status(self, fixture, observation, runner):
        statement = StatementVersion(fixture["problem_id"], fixture["statement_version"], fixture["statement"])
        cert = OpenStatusCertificate(f"status-{fixture['problem_id']}-budget", fixture["problem_id"], fixture["statement_version"], statement.statement_version_id, statement.statement_digest_sha256, (ObservationDigestRef.from_observation(observation),), ProblemStatus(fixture["expected_report_status"]), tuple(fixture["limitations"]), "dogfood-status-reporter", "2026-08-31T11:15:00+00:00", "2026-09-30T00:00:00+00:00")
        dossier = ProblemDossierSnapshot(f"dossier-{fixture['problem_id']}-budget", fixture["problem_id"], fixture["statement_version"], statement, cert, "2026-08-31T11:20:00+00:00")
        validation = dossier.validate({observation.observation_id: observation}, as_of="2026-08-31T12:00:00+00:00", artifacts=runner.literature.artifacts)
        if validation.status is not ProblemStatus.STALE: raise DogfoodArchiveError("budget exhaustion did not preserve evidence insufficiency")
        return {"reported_status": cert.status.value, "validated_status": validation.status.value, "invalidations": [x.value for x in validation.invalidations], "dossier": dossier.to_dict()}

    def _collision_audit(self, fixture, provenance, observations, runner):
        p = next(item for item in provenance if item["source_kind"] == "arxiv-source")
        support = SourceSupport(p["source_id"], p["canonical_uri"], p["pinned_version"], p["locator"], p["content_sha256"])
        routes = tuple(SearchRouteResult(route, f"Dogfood {route.value} scope.", (f"dogfood {route.value}",), (), (), "2026-08-31T12:00:00+00:00", True) for route in SearchRoute)
        record = NoveltyAuditRecord("dogfood-collision-review", CandidateResult("dogfood-collision", digest_json({"statement": fixture["statement"]}), "Reported-resolution review only.", "s1-fixture-v1", (support,)), routes, NoveltyConclusion.PRIOR_RESULT_FOUND, None, "2026-08-31T11:30:00+00:00", "2026-08-31T12:30:00+00:00", NoveltyAuditPurpose.CONTRACT_FIXTURE)
        auth = record.authorization(observations=observations, artifacts=runner.literature.artifacts)
        return {"record": record.to_dict(), "authorization_status": auth.status.value, "complete_research_budget": auth.allows_complete_budget, "public_qualitative_conclusion": auth.allows_public_qualitative_conclusion, "invalidations": [x.value for x in auth.invalidations]}

    def _case(self, fixture, provenance, topic_status, replay_status, status, boundary, manual_reason=None, novelty=None):
        return {"problem_id": fixture["problem_id"], "case_role": fixture["case_role"], "topic_status": topic_status, "replay_status": replay_status, "manual_reason": manual_reason, "review_boundary": boundary, "provenance": provenance, "status": dict(status), "novelty": dict(novelty) if novelty else None, "promotion_allowed": False, "claim_created": False, "trace_created": False}

    def _contract_digest(self): return hashlib.sha256(self.contract_path.read_bytes()).hexdigest()
    def _no_claim_or_trace_created(self): return not any(path.name in {"claims.json", "research-trace.json", "trace.json"} for path in self.root.rglob("*.json"))

    def _replay(self, specs):
        payload = self._load_result()
        if payload["contract_digest_sha256"] != self._contract_digest() or payload["fixture_identity_digest_sha256"] != digest_json(self.contract["fixture_sha256"]) or payload["source_identity_digest_sha256"] != digest_json(specs): raise DogfoodArchiveError("contract or source identity drift on replay")
        main = TopicObservationRunner(self.root / "topic-observation", topic_id=_TOPIC_ID, initial_cursor="dogfood-c0")
        residual_budget = self._new_residual_budget()
        residual = TopicObservationRunner(self.root / "residual-budget", topic_id=_TOPIC_ID, initial_cursor="budget-c0", budget=residual_budget)
        if not (main.next_cursor == "dogfood-c4" and residual.next_cursor == "budget-c1"):
            raise DogfoodArchiveError("topic observation state is missing or has invalid cursor")
        manual_ids = sorted(item.manual_id for item in (*main.manual_queue, *residual.manual_queue))
        if manual_ids != sorted(payload["blocking_manual_ids"]):
            raise DogfoodArchiveError("topic observation manual queue does not match persisted archive")
        if len(main.literature.observations) != 4 or len(residual.literature.observations) != 0:
            raise DogfoodArchiveError("topic observation ArtifactStore state is missing or inconsistent")
        reconstructed_budget = residual_budget.to_dict()
        if self.contract["expected_budget_snapshot"] != reconstructed_budget:
            raise DogfoodArchiveError("reconstructed residual budget does not match T2 contract")
        if payload["budget_snapshot"] != reconstructed_budget:
            raise DogfoodArchiveError("persisted budget snapshot does not match reconstructed residual budget")
        if not payload["no_claim_or_trace_created"] or not self._no_claim_or_trace_created(): raise DogfoodArchiveError("claim or trace artifact is forbidden on replay")
        self._assert_contract_results(payload)
        payload["replayed"] = True; self._save(payload); return payload

    def _assert_contract_results(self, result: Mapping[str, Any]) -> None:
        cases = {case["problem_id"]: case for case in result["cases"]}
        for expected in self.contract["cases"]:
            actual = cases.get(expected["problem_id"])
            if actual is None:
                raise DogfoodArchiveError("persisted result is missing a contract case")
            checks = {
                "case_role": expected["case_role"],
                "topic_status": expected["expected_topic_status"],
                "promotion_allowed": expected["expected_promotion_allowed"],
                "manual_reason": expected["expected_manual_reason"],
            }
            for field, value in checks.items():
                if actual.get(field) != value:
                    raise DogfoodArchiveError(f"contract expected {field}={value!r}, got {actual.get(field)!r}")
            if actual["status"]["reported_status"] != expected["expected_problem_status"]:
                raise DogfoodArchiveError("contract expected problem status drift")
            novelty_status = actual["novelty"]["authorization_status"] if actual["novelty"] else None
            if novelty_status != expected["expected_novelty_status"]:
                raise DogfoodArchiveError("contract expected novelty status drift")

    def _load_result(self):
        try: payload = json.loads(self.result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise DogfoodArchiveError("persisted archive is unreadable") from exc
        if not isinstance(payload, dict): raise DogfoodArchiveError("persisted archive must be an object")
        required = {"schema_version", "topic_id", "contract_digest_sha256", "fixture_identity_digest_sha256", "source_identity_digest_sha256", "fixture_files", "replayed", "archive_blocked", "blocking_manual_ids", "cases", "budget_snapshot", "budget_digest_sha256", "no_claim_or_trace_created", "archive_digest_sha256"}
        _fields(payload, required, "persisted archive")
        if payload["schema_version"] != _SCHEMA_VERSION or payload["topic_id"] != _TOPIC_ID or payload["fixture_files"] != list(_S1_NAMES) or not payload["archive_blocked"]: raise DogfoodArchiveError("persisted archive identity or fixture contract mismatch")
        if payload["budget_digest_sha256"] != self.contract["expected_budget_digest_sha256"]: raise DogfoodArchiveError("persisted budget snapshot identity mismatch")
        if payload["budget_digest_sha256"] != digest_json(payload["budget_snapshot"]): raise DogfoodArchiveError("persisted budget snapshot digest mismatch")
        digest_payload = {k: v for k, v in payload.items() if k not in {"archive_digest_sha256", "replayed"}}
        if payload["archive_digest_sha256"] != digest_json(digest_payload): raise DogfoodArchiveError("persisted archive digest mismatch")
        return payload

    def _save(self, result):
        payload = dict(result); payload.pop("archive_digest_sha256", None); payload["archive_digest_sha256"] = digest_json({k: v for k, v in payload.items() if k != "replayed"})
        temporary = self.result_path.with_suffix(".tmp"); temporary.write_text(canonical_json(payload) + "\n", encoding="utf-8"); os.replace(temporary, self.result_path)
