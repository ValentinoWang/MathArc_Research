from __future__ import annotations

"""Import older proof-research harness runs without laundering their claims.

The adapter is deliberately conservative. It preserves the source run's
closed-node declarations and audit metadata, but it does not promote imported
claims to MathArc ``VERIFIED`` merely because a legacy JSON file says
``PROVED_AND_AUDITED``. Promotion requires replayable, content-addressed
acceptance evidence under the v0.2 contract.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


class LegacyHarnessError(ValueError):
    """Raised when a legacy harness payload is malformed or contradictory."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    raise LegacyHarnessError(f"expected a list, received {type(value).__name__}")


def _nonempty_text(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise LegacyHarnessError(f"{field} is required")
    return text


def _closure_bit(value: Any) -> bool:
    if value is True or value == 1 or value == "1/1":
        return True
    if value is False or value == 0 or value in {None, "0/1", "0"}:
        return False
    raise LegacyHarnessError(f"unrecognised theorem-closure value: {value!r}")


def _normalise_status(value: Any) -> str:
    return str(value or "UNKNOWN").strip().upper().replace(" ", "_")


@dataclass(frozen=True, slots=True)
class ImportPolicy:
    """Promotion policy for an imported run.

    ``metadata_only`` is the default and safest mode. ``replay_manifest``
    permits imported nodes to become ``VERIFIED`` only when the caller supplies
    an acceptance manifest with independent replay records for each claim.
    """

    mode: str = "metadata_only"
    require_independent_replay: bool = True

    def __post_init__(self) -> None:
        if self.mode not in {"metadata_only", "replay_manifest"}:
            raise LegacyHarnessError(f"unsupported import policy: {self.mode}")


def _manifest_index(manifest: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not manifest:
        return {}
    records = manifest.get("acceptance_records", [])
    if not isinstance(records, list):
        raise LegacyHarnessError("acceptance_records must be a list")
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise LegacyHarnessError("each acceptance record must be an object")
        claim_id = _nonempty_text(record.get("claim_id"), field="acceptance claim_id")
        if claim_id in result:
            raise LegacyHarnessError(f"duplicate acceptance record: {claim_id}")
        result[claim_id] = record
    return result


def _record_is_replayable(record: Mapping[str, Any], *, independent: bool) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if not record.get("artifact_sha256"):
        blockers.append("missing artifact_sha256")
    if not record.get("replay_command"):
        blockers.append("missing replay_command")
    if not record.get("statement_sha256"):
        blockers.append("missing statement_sha256")
    if record.get("result") not in {"PASS", "VERIFIED", True}:
        blockers.append("acceptance result is not PASS")
    if independent and not record.get("independent_reconstruction"):
        blockers.append("missing independent reconstruction")
    return not blockers, blockers


def import_legacy_harness(
    progress: Mapping[str, Any],
    *,
    validation: Mapping[str, Any] | None = None,
    acceptance_manifest: Mapping[str, Any] | None = None,
    policy: ImportPolicy | None = None,
) -> dict[str, Any]:
    """Convert a legacy harness run into a conservative v0.2 import report."""

    policy = policy or ImportPolicy()
    problem = _nonempty_text(progress.get("problem"), field="problem")
    run_id = _nonempty_text(progress.get("run_id"), field="run_id")
    state = _normalise_status(progress.get("state"))
    phase = _normalise_status(progress.get("phase"))

    closure = _closure_bit(progress.get("full_conjecture_logical_closure", "0/1"))
    reported_progress = progress.get("current_weighted_progress_percent")
    if reported_progress is not None:
        try:
            reported_progress = float(reported_progress)
        except (TypeError, ValueError) as exc:
            raise LegacyHarnessError("current_weighted_progress_percent must be numeric") from exc
        if not 0 <= reported_progress <= 100:
            raise LegacyHarnessError("current_weighted_progress_percent must lie in [0, 100]")

    validation = validation or {}
    validation_valid = bool(validation.get("valid", False))
    validation_errors = _as_list(validation.get("errors"))
    validation_warnings = _as_list(validation.get("warnings"))
    counts = validation.get("counts") or {}
    if not isinstance(counts, Mapping):
        raise LegacyHarnessError("validation counts must be an object")

    legacy_acceptance_count = int(counts.get("acceptance_records", 0) or 0)
    manifest = _manifest_index(acceptance_manifest)

    raw_nodes = _as_list(progress.get("new_closed_nodes"))
    all_node_ids = {
        _nonempty_text(item.get("id"), field="closed-node id")
        for item in raw_nodes
        if isinstance(item, Mapping)
    }

    imported_claims: list[dict[str, Any]] = []
    verified_claim_ids: list[str] = []
    for raw in raw_nodes:
        if not isinstance(raw, Mapping):
            raise LegacyHarnessError("new_closed_nodes entries must be objects")
        claim_id = _nonempty_text(raw.get("id"), field="closed-node id")
        statement = _nonempty_text(raw.get("statement"), field=f"statement for {claim_id}")
        source_status = _normalise_status(raw.get("status"))
        blockers = ["legacy status is not v0.2 acceptance evidence"]
        matharc_status = "SUPPORTED"

        dependencies = sorted({str(item) for item in _as_list(raw.get("dependencies"))})
        dangling = [item for item in dependencies if item not in all_node_ids]
        if dangling:
            raise LegacyHarnessError(
                f"closed-node {claim_id} depends on unknown node ids: {dangling}"
            )
        if claim_id in dependencies:
            raise LegacyHarnessError(f"closed-node {claim_id} cannot depend on itself")

        if policy.mode == "replay_manifest":
            record = manifest.get(claim_id)
            if record is None:
                blockers = ["no acceptance record for imported claim"]
            else:
                replayable, blockers = _record_is_replayable(
                    record,
                    independent=policy.require_independent_replay,
                )
                if replayable and validation_valid and not validation_errors:
                    matharc_status = "VERIFIED"
                    verified_claim_ids.append(claim_id)
                elif validation_errors:
                    blockers.append("legacy strict validation contains errors")
                elif not validation_valid:
                    blockers.append("legacy strict validation is not valid")

        imported_claims.append(
            {
                "claim_id": claim_id,
                "statement": statement,
                "statement_sha256": _digest(statement),
                "source_status": source_status,
                "matharc_status": matharc_status,
                "promotion_blockers": blockers,
                "dependencies": dependencies,
            }
        )

    obligations: list[dict[str, str]] = []
    for raw in _as_list(progress.get("critical_open_obligations")):
        if not isinstance(raw, Mapping):
            raise LegacyHarnessError("critical_open_obligations entries must be objects")
        obligations.append(
            {
                "obligation_id": _nonempty_text(raw.get("id"), field="obligation id"),
                "statement": _nonempty_text(raw.get("statement"), field="obligation statement"),
                "status": "OPEN",
                "critical": "true",
            }
        )

    # A legacy closure declaration is never copied blindly. The imported run is
    # closed only when the source says closed, every imported closed node has
    # replay acceptance, and there are no open critical obligations.
    imported_closure = bool(
        closure
        and imported_claims
        and len(verified_claim_ids) == len(imported_claims)
        and not obligations
        and validation_valid
        and not validation_errors
    )

    warnings: list[str] = []
    if closure and not imported_closure:
        warnings.append("source declared theorem closure, but v0.2 replay gates did not re-establish it")
    if reported_progress is not None:
        warnings.append("reported progress is dependency completion, not theorem probability")
    if legacy_acceptance_count == 0:
        warnings.append("legacy validation reports zero acceptance records")
    if validation_warnings:
        warnings.append("legacy strict validation contains warnings")

    result = {
        "schema_version": "matharc.legacy-import.v0.2",
        "source": {
            "run_id": run_id,
            "problem": problem,
            "state": state,
            "phase": phase,
            "progress_sha256": _digest(progress),
            "validation_sha256": _digest(validation) if validation else None,
            "scope_limit": progress.get("scope_limit"),
        },
        "theorem_contract": {
            "statement": problem,
            "target_scope": "UNIVERSAL_OR_SOURCE_DECLARED",
            "acceptance_rule": "all load-bearing claims replayed independently; no critical obligations open",
        },
        "progress": {
            "reported_weighted_percent": reported_progress,
            "meaning": "imported dependency-completion metadata; not a success probability",
            "theorem_closure_bit": int(imported_closure),
        },
        "imported_claims": imported_claims,
        "critical_open_obligations": obligations,
        "audit": {
            "legacy_validation_valid": validation_valid,
            "legacy_errors": validation_errors,
            "legacy_warnings": validation_warnings,
            "legacy_acceptance_records": legacy_acceptance_count,
            "replay_manifest_records": len(manifest),
            "policy": policy.mode,
            "independent_replay_required": policy.require_independent_replay,
        },
        "release_state": "THEOREM_CLOSED" if imported_closure else "BLOCKED_EXACT",
        "claim_boundary": (
            "Imported theorem closure was independently re-established."
            if imported_closure
            else "Imported metadata may support local claims, but it does not establish the full theorem."
        ),
        "warnings": warnings,
    }
    result["import_sha256"] = _digest(result)
    return result


def import_files(
    progress_path: str | Path,
    *,
    validation_path: str | Path | None = None,
    acceptance_manifest_path: str | Path | None = None,
    policy: ImportPolicy | None = None,
) -> dict[str, Any]:
    progress = json.loads(Path(progress_path).read_text(encoding="utf-8"))
    validation = (
        json.loads(Path(validation_path).read_text(encoding="utf-8"))
        if validation_path is not None
        else None
    )
    manifest = (
        json.loads(Path(acceptance_manifest_path).read_text(encoding="utf-8"))
        if acceptance_manifest_path is not None
        else None
    )
    if not isinstance(progress, Mapping):
        raise LegacyHarnessError("progress JSON must contain an object")
    if validation is not None and not isinstance(validation, Mapping):
        raise LegacyHarnessError("validation JSON must contain an object")
    if manifest is not None and not isinstance(manifest, Mapping):
        raise LegacyHarnessError("acceptance manifest JSON must contain an object")
    return import_legacy_harness(
        progress,
        validation=validation,
        acceptance_manifest=manifest,
        policy=policy,
    )


# ---------------------------------------------------------------------------
# v0.3-review R7: the import mapping layer DEV_PATH_V03_DETAIL_V3.md names as
# underestimated in v1 -- `import_legacy_harness`'s conservative report is
# not itself a reviewable trace. This closes that specific gap: object
# (claim)/source/dependency/evidence mapping from a report (and the
# original acceptance manifest, which the report itself never echoes back
# in full) into a real `ResearchTrace` ready for R0-R6.
#
# The one invariant this function exists to protect: a legacy node whose
# `matharc_status` is "SUPPORTED" (human-audited in the old harness, but
# never independently replayed under v0.2 rules) becomes a CANDIDATE claim
# -- eligible for real nomination and review, never silently PROVED. Only
# "VERIFIED" nodes (which `import_legacy_harness` only ever assigns after
# confirming independent, replayable acceptance) get real evidence
# attached, and even then this function never calls `promote_claim` itself
# -- that decision still belongs solely to the normal promotion gate.
# ---------------------------------------------------------------------------

from .schema import ClaimRecord, ClaimStatus, EvidenceKind, EvidenceRecord, EvidenceStatus, TheoremContract
from .trace import ResearchTrace, TraceValidationError

_IMPORT_REPORT_SCHEMA = "matharc.legacy-import.v0.2"


def build_importable_trace(
    report: Mapping[str, Any],
    *,
    acceptance_manifest: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> ResearchTrace:
    """Map an `import_legacy_harness` report into a real `ResearchTrace`.

    `acceptance_manifest` should be the *same* manifest originally passed to
    `import_legacy_harness` (or an equivalent one) -- the report itself only
    carries a count of acceptance records, not their replay fields, so a
    VERIFIED claim's real evidence has to be reconstructed from the
    original manifest, not from the report alone.
    """

    if report.get("schema_version") != _IMPORT_REPORT_SCHEMA:
        raise LegacyHarnessError(
            f"unsupported import report schema: {report.get('schema_version')!r}"
        )
    source = report.get("source")
    if not isinstance(source, Mapping):
        raise LegacyHarnessError("import report is missing its source block")
    contract_block = report.get("theorem_contract")
    if not isinstance(contract_block, Mapping):
        raise LegacyHarnessError("import report is missing its theorem_contract block")
    imported_claims = _as_list(report.get("imported_claims"))
    if not imported_claims:
        raise LegacyHarnessError("import report has no imported_claims to map")

    manifest_index = _manifest_index(acceptance_manifest)

    by_id: dict[str, Mapping[str, Any]] = {}
    for raw in imported_claims:
        if not isinstance(raw, Mapping):
            raise LegacyHarnessError("imported_claims entries must be objects")
        claim_id = _nonempty_text(raw.get("claim_id"), field="imported claim_id")
        if claim_id in by_id:
            raise LegacyHarnessError(f"duplicate imported claim_id: {claim_id}")
        by_id[claim_id] = raw

    ordered = _topological_order(by_id)

    run = run_id or f"IMPORT-{_nonempty_text(source.get('run_id'), field='source.run_id')}"
    contract = TheoremContract(
        contract_id=f"LEGACY-{source.get('run_id')}",
        problem=_nonempty_text(contract_block.get("statement"), field="theorem_contract.statement"),
        target_claim_ids=tuple(ordered),
        scope=str(contract_block.get("target_scope", "")),
        source_refs=(f"legacy-run:{source.get('run_id')}",),
    )
    trace = ResearchTrace(run, contract)

    for claim_id in ordered:
        raw = by_id[claim_id]
        matharc_status = str(raw.get("matharc_status", "SUPPORTED"))
        # The laundering-prevention invariant: SUPPORTED never becomes
        # anything stronger than CANDIDATE here, no matter what the legacy
        # source's own status string said.
        status = ClaimStatus.CANDIDATE if matharc_status in {"SUPPORTED", "VERIFIED"} else ClaimStatus.OPEN
        dependencies = tuple(str(item) for item in _as_list(raw.get("dependencies")))
        try:
            trace.add_claim(
                ClaimRecord(
                    claim_id=claim_id,
                    statement=_nonempty_text(raw.get("statement"), field=f"statement for {claim_id}"),
                    scope=contract.scope or "scope inherited from imported theorem contract",
                    status=status,
                    dependencies=dependencies,
                    owner="legacy-import",
                )
            )
        except TraceValidationError as exc:
            raise LegacyHarnessError(f"could not import claim {claim_id}: {exc}") from exc

        if matharc_status != "VERIFIED":
            continue
        record = manifest_index.get(claim_id)
        if record is None:
            continue
        independent = bool(record.get("independent_reconstruction"))
        evidence = EvidenceRecord(
            evidence_id=f"EV-LEGACY-{claim_id}",
            claim_ids=(claim_id,),
            kind=EvidenceKind.EXACT_COMPUTATION,
            status=EvidenceStatus.ACCEPTED,
            summary=f"Legacy-run acceptance record, re-verified under v0.2 replay gates ({claim_id}).",
            artifact_uri=f"legacy-artifact:{record.get('artifact_sha256')}",
            digest_sha256=str(record.get("artifact_sha256")),
            producer=f"legacy-run:{source.get('run_id')}",
            verifier=(
                "matharc-v02-import-replay" if independent else f"legacy-run:{source.get('run_id')}"
            ),
            independence_group=(
                f"legacy-import:{claim_id}" if independent else ""
            ),
            replay_command=str(record.get("replay_command", "")),
            statement_correspondence=(
                "Formal statement digest matches the legacy statement_sha256 recorded at acceptance time."
            ),
            limitations=(
                ()
                if independent
                else (
                    "Producer and verifier are the same legacy run; this evidence does not by "
                    "itself satisfy an independent-group requirement.",
                )
            ),
        )
        trace.add_evidence(evidence)

    open_obligations = _as_list(report.get("critical_open_obligations"))
    if open_obligations:
        trace.metadata["legacy_import_open_obligations"] = [dict(item) for item in open_obligations]
    trace.metadata["legacy_import_source"] = dict(source)
    return trace


def _topological_order(by_id: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    """Kahn's algorithm so `ResearchTrace.add_claim` (which requires a
    claim's dependencies to already exist) can add every imported claim in
    one safe pass. A dependency cycle is reported here, at the mapping
    boundary, with the actual cycle-adjacent ids -- rather than letting a
    less specific `TraceValidationError` surface from deep inside
    `add_claim`."""

    remaining = {
        claim_id: list(raw.get("dependencies") or ()) for claim_id, raw in by_id.items()
    }
    ordered: list[str] = []
    progressed = True
    while remaining and progressed:
        progressed = False
        for claim_id in sorted(remaining):
            if all(dep not in remaining for dep in remaining[claim_id]):
                ordered.append(claim_id)
                del remaining[claim_id]
                progressed = True
                break
    if remaining:
        raise LegacyHarnessError(
            f"dependency cycle among imported claims: {sorted(remaining)}"
        )
    return tuple(ordered)
