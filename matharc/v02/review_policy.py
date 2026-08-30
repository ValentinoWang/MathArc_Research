"""Promotion policy: per-obligation assurance ladder (v0.3-review R4).

Replaces the "max-weight path" framing the spec explicitly rejects (weight
is a scheduling metric, not mathematical necessity -- a low-weight
dependency can still be a load-bearing logical prerequisite). Instead:
every obligation in a claim's `ReviewBundle` (R2) carries a
`required_assurance`; promotion checks that *every* obligation's actually
achieved assurance meets or exceeds what it asks for.

Default policy (spec's own proposal, coded here as the default -- pending
the chief-scientist sign-off the spec itself calls for; see module-level
`DEFAULT_POLICY_STATUS` and the traceability doc for the honest boundary):
a critical claim that closes partly or wholly on HUMAN_AUDIT evidence needs
at least two independent reviewer groups to have approved it.

Trigger / opt-in boundary: this gate only activates for a claim whose
proof-capable accepted evidence includes at least one HUMAN_AUDIT item.
A claim that closes purely on machine evidence (EXACT_CERTIFICATE,
EXACT_COMPUTATION, FORMAL_PROOF, CHECKED_DERIVATION) is completely
unaffected -- this targets exactly the "two independent HUMAN_AUDIT groups
with no governance" loophole IMPROVEMENT_PLAN_V03 names as the system's
largest, not every claim that has ever touched review.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from .review import ObligationVerdictKind, ReviewLifecycleStatus, get_reviewer_roster, reviews_for_claim
from .review_bundle import RequiredAssurance, ReviewBundleError, build_review_bundle
from .schema import EvidenceKind, EvidenceStatus

if TYPE_CHECKING:
    from .trace import ResearchTrace

DEFAULT_POLICY_STATUS = (
    "CODED_DEFAULT_PENDING_CHIEF_SCIENTIST_SIGN_OFF -- this is the policy the "
    "spec itself proposes as a starting point, not a value anyone with the "
    "authority to set promotion policy has actually approved."
)

_MACHINE_EVIDENCE_KINDS = frozenset(
    {
        EvidenceKind.EXACT_CERTIFICATE.value,
        EvidenceKind.EXACT_COMPUTATION.value,
        EvidenceKind.FORMAL_PROOF.value,
        EvidenceKind.CHECKED_DERIVATION.value,
    }
)


class ClosureTrustClass(str, Enum):
    MACHINE = "machine"
    HUMAN = "human"
    MIXED = "mixed"


def _proof_capable_accepted_evidence(trace: "ResearchTrace", claim_id: str) -> tuple[Any, ...]:
    claim = trace.claims.get(claim_id)
    if claim is None:
        return ()
    return tuple(
        trace.evidence[evidence_id]
        for evidence_id in claim.evidence_ids
        if evidence_id in trace.evidence
        and trace.evidence[evidence_id].status is EvidenceStatus.ACCEPTED
        and trace.evidence[evidence_id].kind
        not in {EvidenceKind.NUMERICAL_EXPERIMENT, EvidenceKind.HEURISTIC, EvidenceKind.COUNTEREXAMPLE}
    )


def claim_closure_trust_class(trace: "ResearchTrace", claim_id: str) -> ClosureTrustClass:
    evidence = _proof_capable_accepted_evidence(trace, claim_id)
    kinds = {item.kind.value for item in evidence}
    machine_present = bool(kinds & _MACHINE_EVIDENCE_KINDS)
    human_present = bool(kinds - _MACHINE_EVIDENCE_KINDS)
    if machine_present and human_present:
        return ClosureTrustClass.MIXED
    if human_present:
        return ClosureTrustClass.HUMAN
    return ClosureTrustClass.MACHINE


def review_gate_applies(trace: "ResearchTrace", claim_id: str) -> bool:
    """The R4 gate is opt-in: it only engages when the claim actually
    relies on HUMAN_AUDIT evidence. A pure-machine claim never pays for
    machinery it never asked for."""

    evidence = _proof_capable_accepted_evidence(trace, claim_id)
    return any(item.kind is EvidenceKind.HUMAN_AUDIT for item in evidence)


@dataclass(slots=True, frozen=True)
class ObligationAssuranceSnapshot:
    obligation_id: str
    required_assurance: RequiredAssurance
    achieved_assurance: RequiredAssurance | None
    satisfied: bool
    supporting_reviewer_groups: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "required_assurance": self.required_assurance.value,
            "achieved_assurance": self.achieved_assurance.value if self.achieved_assurance else None,
            "satisfied": self.satisfied,
            "supporting_reviewer_groups": list(self.supporting_reviewer_groups),
        }


def _reviewer_group(trace: "ResearchTrace", roster_version: str, reviewer_id: str) -> str:
    roster = get_reviewer_roster(trace, roster_version)
    if roster is None:
        return ""
    reviewer = roster.get(reviewer_id)
    return reviewer.independence_group if reviewer is not None else ""


def _achieved_human_assurance(count: int) -> RequiredAssurance | None:
    if count >= 2:
        return RequiredAssurance.HUMAN_DOUBLE
    if count >= 1:
        return RequiredAssurance.HUMAN_SINGLE
    return None


def assurance_snapshot_for_claim(
    trace: "ResearchTrace", claim_id: str
) -> tuple[ObligationAssuranceSnapshot, ...]:
    """Rebuild the claim's obligations fresh from current trace state (same
    "re-derive, don't trust a cached decision" convention as F2's
    `promotion_route_blockers`) and, for each, compute what assurance has
    actually been achieved from ACTIVE, current-revision ReviewRecords."""

    claim = trace.claims.get(claim_id)
    if claim is None:
        return ()
    try:
        bundle = build_review_bundle(trace, claim_id, bundle_id=f"assurance-check:{claim_id}")
    except ReviewBundleError:
        return ()

    active_reviews = tuple(
        record
        for record in reviews_for_claim(trace, claim_id)
        if record.lifecycle_status is ReviewLifecycleStatus.ACTIVE
        and record.claim_revision == claim.revision
    )

    snapshots: list[ObligationAssuranceSnapshot] = []
    for obligation in bundle.obligations:
        if obligation.required_assurance is RequiredAssurance.MACHINE_SUFFICIENT:
            # OB-DEP-* today: satisfied iff the underlying machine fact
            # actually holds. The unique promotion authority already
            # independently blocks on an unproved dependency; this
            # snapshot just makes that fact visible per-obligation too.
            dependency_id = obligation.ref.removeprefix("claim:")
            dependency = trace.claims.get(dependency_id)
            satisfied = dependency is not None and dependency.status.value == "PROVED"
            snapshots.append(
                ObligationAssuranceSnapshot(
                    obligation_id=obligation.obligation_id,
                    required_assurance=obligation.required_assurance,
                    achieved_assurance=RequiredAssurance.MACHINE_SUFFICIENT if satisfied else None,
                    satisfied=satisfied,
                )
            )
            continue

        groups: set[str] = set()
        for record in active_reviews:
            verdict = next(
                (item for item in record.verdicts if item.obligation_id == obligation.obligation_id),
                None,
            )
            if verdict is not None and verdict.verdict is ObligationVerdictKind.OK:
                group = _reviewer_group(trace, record.roster_version, record.reviewer_id)
                if group:
                    groups.add(group)
        achieved = _achieved_human_assurance(len(groups))
        satisfied = achieved is not None and (
            (obligation.required_assurance is RequiredAssurance.HUMAN_SINGLE and len(groups) >= 1)
            or (obligation.required_assurance is RequiredAssurance.HUMAN_DOUBLE and len(groups) >= 2)
        )
        snapshots.append(
            ObligationAssuranceSnapshot(
                obligation_id=obligation.obligation_id,
                required_assurance=obligation.required_assurance,
                achieved_assurance=achieved,
                satisfied=satisfied,
                supporting_reviewer_groups=tuple(sorted(groups)),
            )
        )
    return tuple(snapshots)


def assurance_blockers(trace: "ResearchTrace", claim_id: str) -> tuple[str, ...]:
    """Machine-readable, per-obligation promotion blockers. Empty unless
    `review_gate_applies` -- see module docstring for the opt-in trigger."""

    if not review_gate_applies(trace, claim_id):
        return ()
    blockers = []
    for snapshot in assurance_snapshot_for_claim(trace, claim_id):
        if not snapshot.satisfied:
            blockers.append(
                f"claim {claim_id} obligation {snapshot.obligation_id} requires "
                f"{snapshot.required_assurance.value} but only achieved "
                f"{snapshot.achieved_assurance.value if snapshot.achieved_assurance else 'nothing'}"
            )
    return tuple(blockers)
