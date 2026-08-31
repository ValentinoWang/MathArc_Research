"""A metered, consumable budget for one campaign run.

This is the metering half of the improvement plan's cheap-vs-precise
scheduler (docs/IMPROVEMENT_PLAN_V03.md, W1-3): usage is accrued from real
ToolCallRecord timestamps and reported model usage rather than trusted
purely on a worker's self-report.  The full tier-ordered escalation
scheduler (VALIDITY/FAST/PRECISE/ACCEPTANCE, Kendall-tau ranking fidelity)
is a larger, separate effort this ledger is designed to plug into later; on
its own it gives a campaign a hard, honest stop condition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .schema import ToolCallRecord


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


@dataclass(slots=True)
class BudgetLedger:
    wall_seconds_limit: float | None = None
    input_token_limit: int | None = None
    output_token_limit: int | None = None
    cost_usd_limit: float | None = None

    spent_wall_seconds: float = 0.0
    spent_input_tokens: int = 0
    spent_output_tokens: int = 0
    spent_cost_usd: float = 0.0
    tool_call_count: int = 0
    model_call_count: int = 0
    divergent_usage_reports: list[dict[str, Any]] = field(default_factory=list)

    def charge_tool_call(self, record: ToolCallRecord) -> None:
        try:
            started = _parse_iso(record.started_at)
            ended = _parse_iso(record.ended_at)
            self.spent_wall_seconds += max(0.0, (ended - started).total_seconds())
        except ValueError:
            pass
        self.tool_call_count += 1

    def charge_model_usage(self, usage: Mapping[str, Any]) -> None:
        raw_input_tokens = usage.get("input_tokens", 0)
        raw_output_tokens = usage.get("output_tokens", 0)
        input_tokens = int(raw_input_tokens or 0)
        output_tokens = int(raw_output_tokens or 0)
        cost_usd = usage.get("cost_usd")
        if (
            input_tokens < 0
            or output_tokens < 0
            or isinstance(raw_input_tokens, (int, float)) and raw_input_tokens < 0
            or isinstance(raw_output_tokens, (int, float)) and raw_output_tokens < 0
        ):
            raise ValueError("model usage tokens cannot be negative")
        if isinstance(cost_usd, bool) or (cost_usd is not None and not isinstance(cost_usd, (int, float))):
            raise ValueError("cost_usd must be a number when provided")
        if isinstance(cost_usd, (int, float)) and cost_usd < 0:
            raise ValueError("model usage cost_usd cannot be negative")
        self.spent_input_tokens += input_tokens
        self.spent_output_tokens += output_tokens
        if isinstance(cost_usd, (int, float)):
            self.spent_cost_usd += float(cost_usd)
        self.model_call_count += 1

    def reconcile_self_report(
        self,
        *,
        source: str,
        reported: Mapping[str, Any],
        metered: Mapping[str, Any],
        tolerance: float = 0.2,
    ) -> bool:
        """Flag a worker's self-reported usage that diverges from metered usage.

        Returns True if the report was accepted as consistent, False if it was
        flagged into divergent_usage_reports.  A worker that consistently
        under-reports usage should not be trusted for budget accounting even
        though the metered ledger, not the self-report, is authoritative.
        """

        for key in ("input_tokens", "output_tokens"):
            reported_value = float(reported.get(key, 0) or 0)
            metered_value = float(metered.get(key, 0) or 0)
            if metered_value <= 0:
                continue
            if abs(reported_value - metered_value) / metered_value > tolerance:
                self.divergent_usage_reports.append(
                    {
                        "source": source,
                        "field": key,
                        "reported": reported_value,
                        "metered": metered_value,
                    }
                )
                return False
        return True

    def exhausted(self) -> bool:
        if self.wall_seconds_limit is not None and self.spent_wall_seconds >= self.wall_seconds_limit:
            return True
        if self.input_token_limit is not None and self.spent_input_tokens >= self.input_token_limit:
            return True
        if (
            self.output_token_limit is not None
            and self.spent_output_tokens >= self.output_token_limit
        ):
            return True
        if self.cost_usd_limit is not None and self.spent_cost_usd >= self.cost_usd_limit:
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "limits": {
                "wall_seconds": self.wall_seconds_limit,
                "input_tokens": self.input_token_limit,
                "output_tokens": self.output_token_limit,
                "cost_usd": self.cost_usd_limit,
            },
            "spent": {
                "wall_seconds": self.spent_wall_seconds,
                "input_tokens": self.spent_input_tokens,
                "output_tokens": self.spent_output_tokens,
                "cost_usd": self.spent_cost_usd,
                "tool_calls": self.tool_call_count,
                "model_calls": self.model_call_count,
            },
            "divergent_usage_reports": list(self.divergent_usage_reports),
            "exhausted": self.exhausted(),
        }
