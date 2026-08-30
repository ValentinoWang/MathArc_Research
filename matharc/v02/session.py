from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .failure_memory import FailureMemory
from .metrics import compute_research_metrics
from .orchestrator import ResearchOrchestrator, ResearchRoundPlan
from .schema import ToolStatus
from .trace import ResearchTrace, TraceValidationError
from .workers import ProposalWorker, WorkerExecution


@dataclass(slots=True)
class WorkerRoundRecord:
    role: str
    call_id: str
    status: str
    proposal_recorded: bool
    error: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "call_id": self.call_id,
            "status": self.status,
            "proposal_recorded": self.proposal_recorded,
            "error": self.error,
        }


@dataclass(slots=True)
class SessionRoundResult:
    plan: ResearchRoundPlan
    workers: tuple[WorkerRoundRecord, ...]
    before_metrics: dict[str, Any]
    after_metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "workers": [item.to_dict() for item in self.workers],
            "before_metrics": self.before_metrics,
            "after_metrics": self.after_metrics,
            "claim_boundary": (
                "Worker proposals may change candidate/blocking state but cannot promote "
                "a mathematical claim to PROVED."
            ),
        }


class ResearchSession:
    """Execute a transparent multi-worker round over one ResearchTrace."""

    def __init__(
        self,
        trace: ResearchTrace,
        workers: Iterable[ProposalWorker],
        *,
        failure_memory: FailureMemory | None = None,
    ) -> None:
        self.trace = trace
        self.workers = tuple(workers)
        if not self.workers:
            raise ValueError("a research session requires at least one worker")
        roles = [worker.role for worker in self.workers]
        if len(set(roles)) != len(roles):
            raise ValueError("worker roles must be unique within a round")
        self.orchestrator = ResearchOrchestrator(trace, failure_memory)

    def run_round(self) -> SessionRoundResult:
        before = compute_research_metrics(self.trace)
        plan = self.orchestrator.plan_round()
        trace_view = self._trace_view(plan)
        records: list[WorkerRoundRecord] = []
        for worker in self.workers:
            execution = worker.execute(plan, trace_view)
            recorded = False
            error = execution.raw_stderr.strip()
            self.trace.add_tool_call(execution.tool_call)
            if execution.tool_call.status is ToolStatus.PASS and execution.proposal is not None:
                proposal = dict(execution.proposal)
                linked_calls = list(proposal.get("linked_tool_call_ids", []))
                linked_calls.append(execution.tool_call.call_id)
                proposal["linked_tool_call_ids"] = list(dict.fromkeys(linked_calls))
                linked_claims = list(proposal.get("linked_claim_ids", []))
                if plan.focus_claim_id not in linked_claims:
                    linked_claims.append(plan.focus_claim_id)
                proposal["linked_claim_ids"] = linked_claims
                try:
                    self.orchestrator.accept_agent_proposal(
                        role=worker.role,
                        payload=proposal,
                    )
                    recorded = True
                except TraceValidationError as exc:
                    error = f"{error}\nproposal rejected: {exc}".strip()
            records.append(
                WorkerRoundRecord(
                    role=worker.role,
                    call_id=execution.tool_call.call_id,
                    status=execution.tool_call.status.value,
                    proposal_recorded=recorded,
                    error=error,
                )
            )
        after = compute_research_metrics(self.trace)
        return SessionRoundResult(plan, tuple(records), before, after)

    def _trace_view(self, plan: ResearchRoundPlan) -> dict[str, Any]:
        focus = self.trace.claims[plan.focus_claim_id]
        return {
            "run_id": self.trace.run_id,
            "contract": self.trace.contract.to_dict(),
            "focus_claim": focus.to_dict(),
            "dependencies": [
                self.trace.claims[item].to_dict() for item in focus.dependencies
            ],
            "routes": [
                self.trace.routes[item].to_dict()
                for item in focus.route_ids
                if item in self.trace.routes
            ],
            "accepted_evidence": [
                self.trace.evidence[item].to_dict()
                for item in focus.evidence_ids
                if item in self.trace.evidence
            ],
            "recent_failures": [
                item.to_dict()
                for item in self.trace.failures[-10:]
                if item.claim_id == plan.focus_claim_id
                or item.route_id in focus.route_ids
            ],
            "metrics": compute_research_metrics(self.trace),
            "forbidden_authority": ["PROVED", "PROVED_AND_AUDITED"],
        }
