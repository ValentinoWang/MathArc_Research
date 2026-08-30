from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..v02.audit import AuditSeverity
from ..v02.review_bundle import ReviewBundle, ReviewBundleError
from ..v02.workspace import ResearchWorkspace
from ..v02.schema import digest_json
from .claim_map import check_bidirectional_claims, parse_claim_map, parse_latex_claims
from .latex import bibliography_errors, collect_latex_sources, compile_latex
from .models import PublicationBundle


@dataclass(frozen=True, slots=True)
class PublicationAudit:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    readiness: str = "NOT_READY"

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors), "warnings": list(self.warnings),
                "readiness": self.readiness}


def _load_review(path: Path) -> ReviewBundle:
    if path.is_dir():
        from ..v02.review_bundle import verify_review_bundle_files
        return verify_review_bundle_files(path)
    return ReviewBundle.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _component_digest(value: Any) -> str:
    return digest_json(value)


def _latex_preflight(latex: Path, claim_map: Path | None, abstract: Path | None) -> list[str]:
    errors: list[str] = []
    if not latex.is_file():
        return [f"LaTeX source is missing: {latex}"]
    try:
        sources = collect_latex_sources(latex)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    errors.extend(bibliography_errors(latex.parent))
    if re.search(r"(?:/Users/|/home/|[A-Za-z]:\\)", text):
        errors.append("LaTeX source contains an absolute local path")
    if any(token in text.lower() for token in ("your_api_key", "secret_key", "<placeholder>", "todo")):
        errors.append("LaTeX source contains a credential or placeholder token")
    if claim_map is None:
        errors.append("claim map is required for publication audit")
    else:
        try:
            errors.extend(check_bidirectional_claims(parse_claim_map(claim_map), parse_latex_claims(latex, text=text)))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"claim mapping cannot be loaded: {exc}")
    if abstract is not None:
        if not abstract.is_file():
            errors.append(f"abstract file is missing: {abstract}")
        elif len(abstract.read_text(encoding="utf-8")) > 1920:
            errors.append("abstract exceeds 1920 characters")
    return errors


def audit_publication(
    workspace_root: str | Path,
    publication_bundle: str | Path | PublicationBundle,
    *,
    latex: str | Path | None = None,
    claim_map: str | Path | None = None,
    abstract: str | Path | None = None,
    compile_source: bool = False,
) -> PublicationAudit:
    """Run all machine-blocking publication gates and fail closed on errors."""
    errors: list[str] = []
    warnings: list[str] = []
    try:
        workspace = ResearchWorkspace.load(workspace_root)
    except Exception as exc:  # malformed/tampered state is always a blocker
        return PublicationAudit(False, (f"workspace load failed: {exc}",))
    report = workspace.audit(require_current_commit=True)
    errors.extend(issue.message for issue in report.issues if issue.severity is AuditSeverity.ERROR)
    warnings.extend(issue.message for issue in report.issues if issue.severity is AuditSeverity.WARNING)
    try:
        bundle = publication_bundle if isinstance(publication_bundle, PublicationBundle) else PublicationBundle.from_dict(
            json.loads(Path(publication_bundle).read_text(encoding="utf-8")))
    except Exception as exc:
        return PublicationAudit(False, tuple(errors + [f"publication bundle load failed: {exc}"]), tuple(warnings))
    for claim_id, revision in sorted(bundle.claim_revisions.items()):
        claim = workspace.trace.claims.get(claim_id)
        if claim is None:
            errors.append(f"publication references unknown claim {claim_id}")
        elif claim.revision != revision:
            errors.append(f"claim {claim_id} revision mismatch: publication={revision} trace={claim.revision}")
    for ref in bundle.review_bundles:
        if not ref.path:
            errors.append(f"review bundle {ref.bundle_id} has no verification path")
            continue
        try:
            review = _load_review(Path(ref.path))
            if (review.bundle_id, review.claim_id, review.claim_revision, review.bundle_digest_sha256) != (
                ref.bundle_id, ref.claim_id, ref.claim_revision, ref.digest_sha256):
                errors.append(f"review bundle reference mismatch: {ref.bundle_id}")
        except (OSError, ValueError, ReviewBundleError, json.JSONDecodeError) as exc:
            errors.append(f"review bundle {ref.bundle_id} failed verification: {exc}")
    if bundle.workspace_audit_digest and bundle.workspace_audit_digest != _component_digest(report.to_dict()):
        errors.append("workspace audit digest does not match current workspace state")
    digest_expectations = (
        ("source registry", bundle.source_registry_digest, workspace.sources.to_dict()),
        ("object registry", bundle.object_registry_digest, workspace.objects.to_dict()),
        ("artifact manifest", bundle.artifact_manifest_digest, workspace.artifacts.to_dict()),
    )
    for label, expected, current in digest_expectations:
        if expected and expected != _component_digest(current):
            errors.append(f"{label} digest does not match current workspace")
    if latex is None:
        errors.append("LaTeX source is required for publication audit")
    else:
        errors.extend(_latex_preflight(Path(latex), Path(claim_map) if claim_map else None,
                                       Path(abstract) if abstract else None))
        if compile_source:
            compiled, message = compile_latex(latex)
            if not compiled:
                errors.append(message)
    if latex is None and claim_map is not None:
        errors.append("claim map supplied without LaTeX source")
    valid = not errors
    readiness = "TECHNICAL_PREFLIGHT_PASS" if valid else "NOT_READY"
    return PublicationAudit(valid, tuple(errors), tuple(warnings), readiness)
