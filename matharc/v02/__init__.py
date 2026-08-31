"""MathArc Research v0.2 public API with backward-compatible v0.3 contracts.

The package keeps the v0.1 proof-carrying engine available while exposing the
v0.2 research protocol and the first backward-compatible v0.3 falsification
and failure-channel contracts. v0.3 additions remain proposal/evidence
governance primitives; they do not grant any worker proof authority. The
published package version stays at 0.2.0 until the v0.3 acceptance contract
closes.
"""

from .benchmark import BenchmarkComparison, BenchmarkResult, compare_agents
from .failure_channels import (
    FailureChannel,
    FailureChannelError,
    FailureChannelRecord,
    FailureResolution,
    iter_failure_channel_records,
    open_review_gaps,
    record_claim_counterexample,
    record_review_gap,
    record_route_failure,
)
from .source_observation import LicenseStatus, ObservationStatus, SourceObservation, new_observation
from .literature_base import ImportDisposition, ImportResult, LiteratureBase
from .failure_memory import FailureMemory
from .falsification import (
    FalsificationContractError,
    KillTestKind,
    KillTestSpec,
    RouteEvaluationOutcome,
    RouteEvaluationRecord,
    attach_kill_test_spec,
    get_kill_test_spec,
    iter_route_evaluations,
    promotion_route_blockers,
    record_route_evaluation,
)
from .metrics import compute_research_metrics
from .orchestrator import ResearchOrchestrator, ResearchRoundPlan
from .schema import (
    ClaimRecord,
    ClaimStatus,
    EvidenceRecord,
    EvidenceStatus,
    FailureClass,
    FailureRecord,
    PublicReasoningStep,
    ResearchRoute,
    RouteStatus,
    TheoremContract,
    ToolCallRecord,
    ToolStatus,
)
from .trace import PromotionError, ResearchTrace, TraceValidationError, load_trace, save_trace
from .visualization import render_research_dashboard

__all__ = [
    "BenchmarkComparison",
    "BenchmarkResult",
    "ClaimRecord",
    "ClaimStatus",
    "EvidenceRecord",
    "EvidenceStatus",
    "FailureChannel",
    "FailureChannelError",
    "FailureChannelRecord",
    "FailureClass",
    "FailureMemory",
    "FailureRecord",
    "LicenseStatus",
    "FailureResolution",
    "FalsificationContractError",
    "KillTestKind",
    "KillTestSpec",
    "PromotionError",
    "PublicReasoningStep",
    "ResearchOrchestrator",
    "ResearchRoundPlan",
    "ResearchRoute",
    "ResearchTrace",
    "ObservationStatus",
    "RouteEvaluationOutcome",
    "RouteEvaluationRecord",
    "RouteStatus",
    "SourceObservation",
    "TheoremContract",
    "ToolCallRecord",
    "ToolStatus",
    "TraceValidationError",
    "attach_kill_test_spec",
    "compare_agents",
    "compute_research_metrics",
    "get_kill_test_spec",
    "iter_failure_channel_records",
    "iter_route_evaluations",
    "load_trace",
    "open_review_gaps",
    "promotion_route_blockers",
    "record_claim_counterexample",
    "record_review_gap",
    "record_route_evaluation",
    "record_route_failure",
    "render_research_dashboard",
    "save_trace",
    "new_observation",
    "ImportDisposition",
    "ImportResult",
    "LiteratureBase",
]

__version__ = "0.2.0"
