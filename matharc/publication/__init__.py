"""Fail-closed publication readiness primitives.

The publication layer is an aggregation and gate layer.  Mathematical facts
remain owned by :mod:`matharc.v02`; this package only references and audits
those facts for a paper-scoped release candidate.
"""

from .models import (
    EvidenceIntegrity,
    HumanSignoff,
    HumanSignoffState,
    ManuscriptState,
    PublicationBundle,
    ReviewBundleRef,
    ScientificClosure,
    SubmissionRoute,
    TechnicalPreflight,
)
from .gates import PublicationAudit, audit_publication
from .latex import BibliographyWorkflow, available_compilers, compile_latex, detect_bibliography_workflow

__all__ = [
    "EvidenceIntegrity",
    "HumanSignoff",
    "HumanSignoffState",
    "ManuscriptState",
    "PublicationAudit",
    "PublicationBundle",
    "ReviewBundleRef",
    "BibliographyWorkflow",
    "ScientificClosure",
    "SubmissionRoute",
    "TechnicalPreflight",
    "audit_publication",
    "available_compilers",
    "compile_latex",
    "detect_bibliography_workflow",
]
