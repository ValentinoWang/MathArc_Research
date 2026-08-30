"""Review submission packages (v0.3-review R2).

A `ReviewBundle` freezes everything a reviewer needs to judge one claim at
one revision: the statement, the contract-level definitions it depends on,
its dependency chain, all its evidence (with replay commands), a numbered
obligation checklist, and its attack history -- so a reviewer never has to
trust the live, mutable trace while writing a verdict, and so a claim
revision bump (which already invalidates review-derived evidence per R0)
also invalidates any bundle built against the old revision.

Layering note: this module only reads a bare `ResearchTrace`, matching the
review.py/falsification.py convention. "Pinned definitions" therefore means
the `TheoremContract`'s `assumptions`/`non_claims`/`scope` -- the
definitional commitments reachable from a bare trace -- not the
`MathematicalObject` registry, which lives one layer up on
`ResearchWorkspace` and is out of scope here (R3/R6 territory once this is
wrapped by `SecuredResearchWorkspace`).

Determinism is load-bearing: `ReviewBundle.bundle_digest_sha256` must be
byte-identical across two independent builds from the same trace state, so
`created_at` is provenance only (excluded from the digest, matching
`KillTestSpec`'s convention) and every collection is sorted before hashing.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

from .schema import (
    ClaimStatus,
    EvidenceKind,
    EvidenceStatus,
    FailureClass,
    RouteStatus,
    ToolStatus,
    canonical_json,
    digest_json,
    utc_now,
)

if TYPE_CHECKING:
    from .trace import ResearchTrace


class ReviewBundleError(ValueError):
    """Raised when a review bundle cannot be built or fails integrity checks."""


class RequiredAssurance(str, Enum):
    """What grade of judgement an obligation needs. R2 only assigns this
    label; R4 is where the promotion policy reads it and enforces a floor."""

    MACHINE_SUFFICIENT = "MACHINE_SUFFICIENT"
    HUMAN_SINGLE = "HUMAN_SINGLE"
    HUMAN_DOUBLE = "HUMAN_DOUBLE"


def _strict_keys(cls: type[Any], payload: Mapping[str, Any]) -> None:
    allowed = {item.name for item in fields(cls)}
    unknown = set(payload) - allowed
    if unknown:
        raise ReviewBundleError(f"unknown fields for {cls.__name__}: {sorted(unknown)}")


def _tuple_of_str(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise ReviewBundleError("expected an array of strings, not a string")
    return tuple(str(item) for item in value)


@dataclass(slots=True, frozen=True)
class Obligation:
    obligation_id: str
    title: str
    ask: str
    points: tuple[str, ...]
    ref: str
    required_assurance: RequiredAssurance

    def __post_init__(self) -> None:
        if not self.obligation_id.strip() or not self.title.strip() or not self.ask.strip():
            raise ReviewBundleError("obligation_id, title and ask are required")
        if not self.points:
            raise ReviewBundleError(f"obligation {self.obligation_id} needs at least one point")

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "title": self.title,
            "ask": self.ask,
            "points": list(self.points),
            "ref": self.ref,
            "required_assurance": self.required_assurance.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Obligation":
        _strict_keys(cls, payload)
        return cls(
            obligation_id=str(payload["obligation_id"]),
            title=str(payload["title"]),
            ask=str(payload["ask"]),
            points=_tuple_of_str(payload["points"]),
            ref=str(payload.get("ref", "")),
            required_assurance=RequiredAssurance(str(payload["required_assurance"])),
        )


@dataclass(slots=True, frozen=True)
class AttackHistoryItem:
    attack_id: str
    summary: str
    emphasis: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.attack_id.strip() or not self.summary.strip():
            raise ReviewBundleError("attack_id and summary are required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "attack_id": self.attack_id,
            "summary": self.summary,
            "emphasis": list(self.emphasis),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AttackHistoryItem":
        _strict_keys(cls, payload)
        return cls(
            attack_id=str(payload["attack_id"]),
            summary=str(payload["summary"]),
            emphasis=_tuple_of_str(payload.get("emphasis")),
        )


@dataclass(slots=True, frozen=True)
class ReviewBundle:
    bundle_id: str
    claim_id: str
    claim_revision: int
    statement: str
    scope: str
    boundary: str
    pinned_definitions: Mapping[str, Any]
    dependency_path: tuple[Mapping[str, Any], ...]
    evidence: tuple[Mapping[str, Any], ...]
    obligations: tuple[Obligation, ...]
    attack_history: tuple[AttackHistoryItem, ...]
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.bundle_id.strip() or not self.claim_id.strip():
            raise ReviewBundleError("bundle_id and claim_id are required")
        obligation_ids = [item.obligation_id for item in self.obligations]
        if len(obligation_ids) != len(set(obligation_ids)):
            raise ReviewBundleError("duplicate obligation_id in bundle")
        statement_obligations = [
            item for item in self.obligations if item.obligation_id == "OB-STATEMENT-CORRESPONDENCE"
        ]
        if not statement_obligations:
            raise ReviewBundleError(
                "every bundle must carry an explicit statement-correspondence obligation "
                "as its own numbered item"
            )

    def _files(self) -> dict[str, Any]:
        """Logical file → canonical content, matching what gets written to
        disk by `write_review_bundle`. Deterministic: no timestamps, sorted
        collections."""

        return {
            "statement.json": {
                "claim_id": self.claim_id,
                "claim_revision": self.claim_revision,
                "statement": self.statement,
                "scope": self.scope,
                "boundary": self.boundary,
            },
            "definitions.json": dict(self.pinned_definitions),
            "dependencies.json": list(self.dependency_path),
            "evidence.json": list(self.evidence),
            "obligations.json": [item.to_dict() for item in self.obligations],
            "attacks.json": [item.to_dict() for item in self.attack_history],
        }

    def file_digests(self) -> dict[str, str]:
        return {name: digest_json(content) for name, content in self._files().items()}

    @property
    def bundle_digest_sha256(self) -> str:
        return digest_json(self.file_digests())

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "claim_id": self.claim_id,
            "claim_revision": self.claim_revision,
            "statement": self.statement,
            "scope": self.scope,
            "boundary": self.boundary,
            "pinned_definitions": dict(self.pinned_definitions),
            "dependency_path": list(self.dependency_path),
            "evidence": list(self.evidence),
            "obligations": [item.to_dict() for item in self.obligations],
            "attack_history": [item.to_dict() for item in self.attack_history],
            "bundle_digest_sha256": self.bundle_digest_sha256,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReviewBundle":
        allowed = {item.name for item in fields(cls)} | {"bundle_digest_sha256"}
        unknown = set(payload) - allowed
        if unknown:
            raise ReviewBundleError(f"unknown fields for ReviewBundle: {sorted(unknown)}")
        raw_obligations = payload.get("obligations", ())
        raw_attacks = payload.get("attack_history", ())
        if isinstance(raw_obligations, Mapping) or isinstance(raw_attacks, Mapping):
            raise ReviewBundleError("obligations/attack_history must be arrays")
        bundle = cls(
            bundle_id=str(payload["bundle_id"]),
            claim_id=str(payload["claim_id"]),
            claim_revision=int(payload.get("claim_revision", 0)),
            statement=str(payload["statement"]),
            scope=str(payload.get("scope", "")),
            boundary=str(payload.get("boundary", "")),
            pinned_definitions=dict(payload.get("pinned_definitions", {})),
            dependency_path=tuple(dict(item) for item in payload.get("dependency_path", ())),
            evidence=tuple(dict(item) for item in payload.get("evidence", ())),
            obligations=tuple(Obligation.from_dict(item) for item in raw_obligations),
            attack_history=tuple(AttackHistoryItem.from_dict(item) for item in raw_attacks),
            created_at=str(payload.get("created_at") or utc_now()),
        )
        expected_digest = str(payload.get("bundle_digest_sha256", ""))
        if expected_digest and expected_digest != bundle.bundle_digest_sha256:
            raise ReviewBundleError("bundle_digest_sha256 does not match the bundle's own content")
        return bundle


def _dependency_snapshot(trace: "ResearchTrace", claim_id: str) -> dict[str, Any]:
    claim = trace.claims[claim_id]
    return {
        "claim_id": claim.claim_id,
        "statement": claim.statement,
        "status": claim.status.value,
        "revision": claim.revision,
    }


def _ordered_dependency_path(trace: "ResearchTrace", claim_id: str) -> tuple[dict[str, Any], ...]:
    """Every ancestor the claim's proof depends on, topologically ordered by
    a stable key (claim_id) so the bundle is deterministic regardless of
    dict insertion order."""

    seen: set[str] = set()
    ordered: list[str] = []

    def visit(current_id: str) -> None:
        claim = trace.claims.get(current_id)
        if claim is None:
            return
        for dependency_id in sorted(claim.dependencies):
            if dependency_id not in seen:
                seen.add(dependency_id)
                visit(dependency_id)
                ordered.append(dependency_id)

    visit(claim_id)
    return tuple(_dependency_snapshot(trace, item) for item in ordered)


# Rule 4 in practice: an obligation's reviewer-facing text must not embed a
# raw backend enum value; every kind/status that can appear here gets an
# explicit daily-language label instead. Deliberately not derived from
# `.value` automatically -- the whole point is that a new enum member
# forces someone to write a human sentence for it, not silently leak.
_EVIDENCE_KIND_LABELS: dict[str, str] = {
    "LITERATURE_RESULT": "引用外部文献的结论",
    "HUMAN_AUDIT": "专家人工审核的结论",
    "NUMERICAL_EXPERIMENT": "数值实验观察",
    "HEURISTIC": "启发式判断，未经严格证明",
    "COUNTEREXAMPLE": "反例记录",
    "CHECKED_DERIVATION": "经检查的推导",
}


def _evidence_kind_label(kind_value: str) -> str:
    return _EVIDENCE_KIND_LABELS.get(kind_value, "非机器可验证的证据")


def _default_obligations(
    trace: "ResearchTrace",
    claim_id: str,
    *,
    non_machine_evidence_assurance: RequiredAssurance,
) -> tuple[Obligation, ...]:
    from .falsification import get_kill_test_spec
    from .review import is_review_derived_evidence

    claim = trace.claims[claim_id]
    obligations: list[Obligation] = [
        Obligation(
            obligation_id="OB-STATEMENT-CORRESPONDENCE",
            title="语句对应",
            ask="送审包里冻结的正式语句，是否和它声称要证明的非正式命题是同一件事？",
            points=(
                "范围声明是否覆盖了原始描述里实际要求的全部情形，没有偷偷缩小。",
                "边界声明是否如实排除了未处理的情形，没有偷偷扩大。",
                "有没有把「在有限样例上验证」悄悄写成「对全部情形成立」。",
            ),
            ref=f"claim:{claim.claim_id}",
            required_assurance=RequiredAssurance.HUMAN_SINGLE,
        )
    ]
    for dependency_id in sorted(claim.dependencies):
        dependency = trace.claims.get(dependency_id)
        if dependency is None:
            continue
        already_closed = dependency.status is ClaimStatus.PROVED
        obligations.append(
            Obligation(
                obligation_id=f"OB-DEP-{dependency_id}",
                title="依赖项是否已闭合",
                ask="这个结论依赖另一个结论。请确认那个结论已经走完自己的证明流程，而不是还在半路上。",
                points=(
                    "已闭合。"
                    if already_closed
                    else "尚未闭合——只要这一步没完成，整条证明链条就是不完整的。",
                ),
                ref=f"claim:{dependency_id}",
                required_assurance=RequiredAssurance.MACHINE_SUFFICIENT,
            )
        )
    for route_id in sorted(claim.route_ids):
        route = trace.routes.get(route_id)
        if route is None:
            continue
        spec = get_kill_test_spec(trace, route_id)
        if spec is None:
            continue
        obligations.append(
            Obligation(
                obligation_id=f"OB-ROUTE-{route_id}",
                title="证伪测试是否可信",
                ask="这条路线用来抓反例的测试，本身设计是否合理？它真的会在命题为假时抓到反例吗？",
                points=(
                    f"测试范围：{spec.tested_scope}——请确认结论没有被悄悄外推到这个范围之外。",
                    "测试执行记录是否真的对应这条路线的当前版本，而不是一份过期记录。",
                ),
                ref=f"route:{route_id}（{route.name}）",
                required_assurance=RequiredAssurance.HUMAN_SINGLE,
            )
        )
    for evidence_id in sorted(claim.evidence_ids):
        evidence = trace.evidence.get(evidence_id)
        if evidence is None or evidence.status is not EvidenceStatus.ACCEPTED:
            continue
        if evidence.kind.value in {"EXACT_CERTIFICATE", "EXACT_COMPUTATION", "FORMAL_PROOF"}:
            continue
        if is_review_derived_evidence(trace, evidence_id):
            # A review's own resulting HUMAN_AUDIT evidence must not demand
            # a second "please independently assess this evidence" pass on
            # itself -- that would be circular. Its legitimacy is already
            # governed by the review lifecycle and by
            # OB-STATEMENT-CORRESPONDENCE/OB-INDEPENDENCE above.
            continue
        kind_label = _evidence_kind_label(evidence.kind.value)
        obligations.append(
            Obligation(
                obligation_id=f"OB-EVIDENCE-{evidence_id}",
                title="这条证据真的支持结论吗",
                ask="请独立复核这条证据，不要只看它的摘要文字。",
                points=(
                    f"这是一条{kind_label}，不属于可机器验证的档位，需要你独立判断其可信度。",
                    "产出这条证据的人和核实它的人，是否真的是两个互不重叠的独立来源。",
                ),
                ref=f"evidence:{evidence_id}（{evidence.kind.value}）",
                required_assurance=non_machine_evidence_assurance,
            )
        )
    if claim.critical:
        obligations.append(
            Obligation(
                obligation_id="OB-INDEPENDENCE",
                title="独立性",
                ask="这是关键（critical）claim。请确认支持它的证据确实来自至少两个互不重叠的独立来源。",
                points=(
                    "同一个人/同一次运行产出的两份材料不算两个独立来源；",
                    "两个独立来源应当在方法或视角上真的不同，而不是同一方法跑两次。",
                ),
                ref=f"claim:{claim.claim_id}",
                required_assurance=RequiredAssurance.HUMAN_DOUBLE,
            )
        )
    return tuple(obligations)


def build_review_bundle(
    trace: "ResearchTrace",
    claim_id: str,
    *,
    bundle_id: str,
    attack_history: tuple[AttackHistoryItem, ...] = (),
    non_machine_evidence_assurance: RequiredAssurance = RequiredAssurance.HUMAN_SINGLE,
) -> ReviewBundle:
    """Deterministic: calling this twice against the same trace state and
    the same `bundle_id`/`attack_history` produces byte-identical
    `bundle_digest_sha256`."""

    claim = trace.claims.get(claim_id)
    if claim is None:
        raise ReviewBundleError(f"unknown claim: {claim_id}")
    contract = trace.contract
    pinned_definitions = {
        "problem": contract.problem,
        "contract_scope": contract.scope,
        "assumptions": sorted(contract.assumptions),
        "non_claims": sorted(contract.non_claims),
    }
    evidence_snapshots = tuple(
        trace.evidence[evidence_id].to_dict()
        for evidence_id in sorted(claim.evidence_ids)
        if evidence_id in trace.evidence
    )
    obligations = _default_obligations(
        trace, claim_id, non_machine_evidence_assurance=non_machine_evidence_assurance
    )
    return ReviewBundle(
        bundle_id=bundle_id,
        claim_id=claim_id,
        claim_revision=claim.revision,
        statement=claim.statement,
        scope=claim.scope,
        boundary=claim.boundary,
        pinned_definitions=pinned_definitions,
        dependency_path=_ordered_dependency_path(trace, claim_id),
        evidence=evidence_snapshots,
        obligations=obligations,
        attack_history=tuple(sorted(attack_history, key=lambda item: item.attack_id)),
    )


# --------------------------------------------------------------------------
# On-disk packaging with per-file SHA-256 and a sealed manifest.
# --------------------------------------------------------------------------

_MANIFEST_NAME = "manifest.json"


def write_review_bundle(bundle: ReviewBundle, out_dir: str | Path) -> dict[str, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    files = bundle._files()
    written: dict[str, Path] = {}
    file_hashes: dict[str, str] = {}
    for name, content in files.items():
        path = target / name
        text = json.dumps(content, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        path.write_text(text, encoding="utf-8")
        written[name] = path
        file_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "schema_version": "1.0",
        "bundle_id": bundle.bundle_id,
        "claim_id": bundle.claim_id,
        "claim_revision": bundle.claim_revision,
        "file_sha256": file_hashes,
        "bundle_digest_sha256": bundle.bundle_digest_sha256,
        "created_at": bundle.created_at,
    }
    manifest_path = target / _MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    written[_MANIFEST_NAME] = manifest_path
    return written


def verify_review_bundle_files(out_dir: str | Path) -> ReviewBundle:
    """Re-read every file, recompute its SHA-256, and compare against the
    sealed manifest -- and recompute the bundle from its own file content
    and compare that digest too. Raises ReviewBundleError on any
    single-byte tamper, in either the manifest or any file it covers."""

    target = Path(out_dir)
    manifest_path = target / _MANIFEST_NAME
    if not manifest_path.is_file():
        raise ReviewBundleError(f"missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    file_hashes = manifest.get("file_sha256", {})
    if not isinstance(file_hashes, Mapping):
        raise ReviewBundleError("manifest file_sha256 is malformed")

    contents: dict[str, Any] = {}
    for name, expected_hash in file_hashes.items():
        path = target / str(name)
        if not path.is_file():
            raise ReviewBundleError(f"bundle file missing: {name}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ReviewBundleError(f"bundle file tampered: {name}")
        contents[str(name)] = json.loads(path.read_text(encoding="utf-8"))

    reconstructed = ReviewBundle(
        bundle_id=str(manifest["bundle_id"]),
        claim_id=str(contents["statement.json"]["claim_id"]),
        claim_revision=int(contents["statement.json"]["claim_revision"]),
        statement=str(contents["statement.json"]["statement"]),
        scope=str(contents["statement.json"].get("scope", "")),
        boundary=str(contents["statement.json"].get("boundary", "")),
        pinned_definitions=dict(contents["definitions.json"]),
        dependency_path=tuple(contents["dependencies.json"]),
        evidence=tuple(contents["evidence.json"]),
        obligations=tuple(Obligation.from_dict(item) for item in contents["obligations.json"]),
        attack_history=tuple(AttackHistoryItem.from_dict(item) for item in contents["attacks.json"]),
        created_at=str(manifest.get("created_at") or utc_now()),
    )
    expected_bundle_digest = str(manifest.get("bundle_digest_sha256", ""))
    if reconstructed.bundle_digest_sha256 != expected_bundle_digest:
        raise ReviewBundleError(
            "manifest bundle_digest_sha256 does not match the bundle reconstructed from its own files"
        )
    return reconstructed


# --------------------------------------------------------------------------
# Reviewer-facing copy rules (DEV_PATH_V03_DETAIL_V3.md appendix A, R2
# acceptance item: "义务文案通过下方文案规范的自动检查"). Applies to
# obligations and attack-history summaries -- the two prose layers a
# reviewer reads directly. Evidence entries stay as technical-detail JSON
# (backend field names as JSON keys are expected there) and are out of
# scope for this checker.
# --------------------------------------------------------------------------

# Rule 1: backend status enum values must never appear in reviewer-facing
# prose. Derived from the actual enums rather than hand-copied, so it can't
# drift out of sync with schema.py the way a literal string list would.
_BACKEND_ENUM_TOKENS: frozenset[str] = frozenset(
    member.value
    for enum_cls in (ClaimStatus, RouteStatus, EvidenceStatus, EvidenceKind, ToolStatus, FailureClass)
    for member in enum_cls
)

# Rule 1 also bans backend field names, independent of any specific enum.
_BACKEND_FIELD_NAME_PATTERN = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")

# A generic ALL_CAPS_WITH_UNDERSCORE token (object ids, status literals not
# already covered by an enum, etc.).
_SCREAMING_SNAKE_PATTERN = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")

# Any contiguous run of ASCII letters -- used to pull enum-shaped tokens
# like "FALSIFIED" out of Chinese prose. Deliberately not `\b`-delimited:
# Python's `\b` treats CJK characters as "word" characters too, so a token
# glued directly onto Chinese text with no space (a very common real case,
# e.g. "...是 FALSIFIED，请...") would not get a boundary there at all and
# would slip past a `\b`-anchored pattern. A bare run of `[A-Za-z]` needs no
# boundary: CJK characters simply aren't in that character class.
_ASCII_WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9]*")

# Rule 4: internal jargon that must be paraphrased for a reviewer who has
# never read this codebase.
_JARGON_TERMS: tuple[str, ...] = (
    "kill test",
    "越级",
    "洗白通道",
    "钉定",
    "规范形",
    "审计层",
)

# Rule 2: a quoted run of 3+ space-separated ASCII words is presumed to be
# an untranslated foreign-language quote; if `ref` doesn't carry the
# required disclaimer, it must not appear in reviewer-facing prose.
_ASCII_QUOTE_PATTERN = re.compile(r"[\"“]([A-Za-z][A-Za-z0-9 ,.'\-]*[A-Za-z0-9.])[\"”]")
_REQUIRED_FOREIGN_QUOTE_DISCLAIMER = "原文为英文，可在证据区查看"

_MAX_TITLE_CHARS = 20


def _copy_violations(*, title: str, ask: str, points: tuple[str, ...], ref: str) -> tuple[str, ...]:
    violations: list[str] = []
    body_segments = (title, ask, *points)
    full_body = "\n".join(body_segments)

    if len(title) > _MAX_TITLE_CHARS:
        violations.append(f"标题超过 {_MAX_TITLE_CHARS} 字（一条义务只应问一个问题）：{title!r}")

    for segment in body_segments:
        screaming = _SCREAMING_SNAKE_PATTERN.findall(segment)
        field_like = _BACKEND_FIELD_NAME_PATTERN.findall(segment)
        enum_hits = [word for word in _ASCII_WORD_PATTERN.findall(segment) if word in _BACKEND_ENUM_TOKENS]
        offenders = sorted(set(screaming) | set(field_like) | set(enum_hits))
        if offenders:
            violations.append(f"正文出现后端标识符/枚举值，应改成自然语言：{offenders} in {segment!r}")

    for point in points:
        semicolons = point.count("；") + point.count(";")
        if semicolons >= 2:
            violations.append(f"一个要点里用分号挤进了三件以上的事：{point!r}")

    quotes = _ASCII_QUOTE_PATTERN.findall(full_body)
    long_quotes = [item for item in quotes if len(item.split()) >= 3]
    if long_quotes and _REQUIRED_FOREIGN_QUOTE_DISCLAIMER not in ref:
        violations.append(
            f"正文直接嵌入了未翻译的英文原句 {long_quotes!r}，应改成中文转述，"
            f"原文放证据区并在 ref 里写明「{_REQUIRED_FOREIGN_QUOTE_DISCLAIMER}」"
        )

    for term in _JARGON_TERMS:
        if term in full_body:
            violations.append(f"出现内部黑话「{term}」，应换成评审人看得懂的日常说法")

    return tuple(violations)


def check_obligation_copy(obligation: Obligation) -> tuple[str, ...]:
    """Machine-checkable subset of appendix A's copy rules. Returns an
    empty tuple when the obligation's reviewer-facing prose is clean."""

    return _copy_violations(
        title=obligation.title,
        ask=obligation.ask,
        points=obligation.points,
        ref=obligation.ref,
    )


def check_attack_history_copy(item: AttackHistoryItem) -> tuple[str, ...]:
    return _copy_violations(title="", ask=item.summary, points=item.emphasis, ref="")


_REQUIRED_ASSURANCE_LABELS: dict[str, str] = {
    RequiredAssurance.MACHINE_SUFFICIENT.value: "机器已核实",
    RequiredAssurance.HUMAN_SINGLE.value: "需要一位评审人判断",
    RequiredAssurance.HUMAN_DOUBLE.value: "需要两位独立评审人分别判断",
}


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_review_bundle_html(bundle: ReviewBundle, out_path: str | Path) -> Path:
    """Self-contained, static HTML view so a reviewer never has to read the
    bundle's raw JSON. Deliberately reuses the color/type tokens already
    established and frozen in `docs/prototypes/review-console.html`
    (`FROZEN_RECRUITING_DEMO`) rather than proposing a new visual system --
    this is an instantiation of that design with real bundle data, not a
    redesign, so it does not count against the freeze. No JavaScript:
    progressive disclosure / live interactivity is R6's job once this is
    served from a real endpoint; a mailed/archived review package is static
    by nature anyway."""

    def obligation_block(item: Obligation) -> str:
        points_html = "".join(f"<li>{_html_escape(point)}</li>" for point in item.points)
        assurance_label = _REQUIRED_ASSURANCE_LABELS.get(
            item.required_assurance.value, item.required_assurance.value
        )
        ref_html = (
            f'<p class="ref">对照对象：{_html_escape(item.ref)}</p>' if item.ref else ""
        )
        return f"""
        <article class="obligation">
          <h3>{_html_escape(item.title)}</h3>
          <p class="assurance">{_html_escape(assurance_label)}</p>
          <p class="ask">{_html_escape(item.ask)}</p>
          <ul>{points_html}</ul>
          {ref_html}
        </article>"""

    def attack_block(item: AttackHistoryItem) -> str:
        emphasis_html = "".join(f"<li>{_html_escape(point)}</li>" for point in item.emphasis)
        return f"""
        <article class="attack">
          <p>{_html_escape(item.summary)}</p>
          <ul>{emphasis_html}</ul>
        </article>"""

    def dependency_row(item: Mapping[str, Any]) -> str:
        return (
            f"<tr><td>{_html_escape(str(item.get('claim_id', '')))}</td>"
            f"<td>{_html_escape(str(item.get('statement', '')))}</td>"
            f"<td>{_html_escape(str(item.get('status', '')))}</td></tr>"
        )

    obligations_html = "".join(obligation_block(item) for item in bundle.obligations)
    attacks_html = "".join(attack_block(item) for item in bundle.attack_history) or (
        '<p class="empty">（这条结论目前没有记录在案的攻击史。）</p>'
    )
    dependency_rows = "".join(dependency_row(item) for item in bundle.dependency_path) or (
        '<tr><td colspan="3" class="empty">（没有依赖项。）</td></tr>'
    )

    html = f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>送审包 · {_html_escape(bundle.claim_id)}</title>
<style>
:root {{
  --ground: #F4F7F6; --surface: #FFFFFF; --surface-2: #EDF2F0;
  --ink: #1C2B2D; --muted: #5E7173; --line: #D5DEDC;
  --accent: #0F6B62; --accent-strong: #0A544D; --accent-soft: #E2EFEC;
  --serif: "Noto Serif SC", "Songti SC", "SimSun", serif;
  --sans: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  --mono: "JetBrains Mono", ui-monospace, "SF Mono", Consolas, monospace;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--ground); color: var(--ink); font-family: var(--sans); line-height: 1.6; }}
header {{ background: var(--accent); color: #fff; padding: 24px 32px; }}
header h1 {{ font-family: var(--serif); margin: 0 0 4px; font-size: 22px; }}
header p {{ margin: 0; opacity: .85; font-size: 13px; font-family: var(--mono); }}
main {{ max-width: 860px; margin: 0 auto; padding: 24px 32px 64px; }}
section {{ margin-top: 32px; }}
section > h2 {{ font-family: var(--serif); font-size: 18px; border-bottom: 1px solid var(--line); padding-bottom: 8px; }}
.obligation, .attack {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 16px 20px; margin-bottom: 12px; }}
.obligation h3 {{ margin: 0 0 6px; font-size: 16px; }}
.assurance {{ display: inline-block; background: var(--accent-soft); color: var(--accent-strong); font-size: 12px; padding: 2px 8px; border-radius: 999px; margin-bottom: 8px; }}
.ask {{ color: var(--muted); margin: 0 0 8px; }}
ul {{ margin: 0; padding-left: 20px; }}
.ref {{ font-family: var(--mono); font-size: 12px; color: var(--muted); margin: 8px 0 0; }}
table {{ width: 100%; border-collapse: collapse; background: var(--surface); }}
td {{ border-bottom: 1px solid var(--line); padding: 8px 10px; font-size: 14px; }}
.empty {{ color: var(--muted); font-style: italic; }}
.boundary {{ background: var(--surface-2); border-radius: 8px; padding: 16px 20px; font-size: 13px; color: var(--muted); }}
</style>
</head>
<body>
<header>
  <h1>送审包 · {_html_escape(bundle.statement)}</h1>
  <p>claim {_html_escape(bundle.claim_id)} · 第 {bundle.claim_revision} 版 · 包摘要 {bundle.bundle_digest_sha256}</p>
</header>
<main>
  <section>
    <h2>范围与边界</h2>
    <p><strong>范围：</strong>{_html_escape(bundle.scope)}</p>
    <p><strong>边界：</strong>{_html_escape(bundle.boundary) or "（未声明）"}</p>
  </section>
  <section>
    <h2>需要评审人判断的事项</h2>
    {obligations_html}
  </section>
  <section>
    <h2>依赖链</h2>
    <table>{dependency_rows}</table>
  </section>
  <section>
    <h2>此前的攻击史</h2>
    {attacks_html}
  </section>
  <section class="boundary">
    这份送审包是在 claim 第 {bundle.claim_revision} 版时冻结生成的；claim 语句一旦修订，这份包和据此产出的评审记录都会自动失效，不会被悄悄当作仍然适用。
  </section>
</main>
</body>
</html>
"""
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return target


def check_bundle_copy(bundle: ReviewBundle) -> dict[str, tuple[str, ...]]:
    """All copy-rule violations across the bundle's reviewer-facing prose,
    keyed by obligation_id/attack_id. Empty dict means the bundle is clean
    -- this is the automated gate the R2 acceptance criteria ask for."""

    findings: dict[str, tuple[str, ...]] = {}
    for obligation in bundle.obligations:
        violations = check_obligation_copy(obligation)
        if violations:
            findings[obligation.obligation_id] = violations
    for item in bundle.attack_history:
        violations = check_attack_history_copy(item)
        if violations:
            findings[item.attack_id] = violations
    return findings
