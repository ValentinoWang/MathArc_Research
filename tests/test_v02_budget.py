from __future__ import annotations

import unittest

from matharc.v02.budget import BudgetLedger
from matharc.v02.schema import ToolCallRecord, ToolStatus


def tool_call(started: str, ended: str) -> ToolCallRecord:
    return ToolCallRecord(
        call_id="T",
        tool="exact:test",
        purpose="test",
        status=ToolStatus.PASS,
        input_digest_sha256="a" * 64,
        output_digest_sha256="b" * 64,
        linked_claim_ids=("C",),
        independence_group="test",
        replay_command="true",
        started_at=started,
        ended_at=ended,
    )


class BudgetLedgerTests(unittest.TestCase):
    def test_wall_seconds_are_metered_from_tool_call_timestamps(self) -> None:
        ledger = BudgetLedger(wall_seconds_limit=10.0)
        ledger.charge_tool_call(
            tool_call("2026-01-01T00:00:00+00:00", "2026-01-01T00:00:04+00:00")
        )
        self.assertAlmostEqual(ledger.spent_wall_seconds, 4.0)
        self.assertFalse(ledger.exhausted())
        ledger.charge_tool_call(
            tool_call("2026-01-01T00:00:00+00:00", "2026-01-01T00:00:07+00:00")
        )
        self.assertTrue(ledger.exhausted())

    def test_model_usage_and_cost_are_accumulated(self) -> None:
        ledger = BudgetLedger(cost_usd_limit=1.0)
        ledger.charge_model_usage({"input_tokens": 100, "output_tokens": 50, "cost_usd": 0.6})
        self.assertFalse(ledger.exhausted())
        ledger.charge_model_usage({"input_tokens": 100, "output_tokens": 50, "cost_usd": 0.6})
        self.assertTrue(ledger.exhausted())
        self.assertEqual(ledger.spent_input_tokens, 200)
        self.assertEqual(ledger.model_call_count, 2)

    def test_no_limits_never_exhausts(self) -> None:
        ledger = BudgetLedger()
        ledger.charge_model_usage({"input_tokens": 10_000_000, "cost_usd": 1_000.0})
        self.assertFalse(ledger.exhausted())

    def test_reconcile_flags_large_divergence(self) -> None:
        ledger = BudgetLedger()
        accepted = ledger.reconcile_self_report(
            source="worker-a",
            reported={"input_tokens": 100},
            metered={"input_tokens": 105},
        )
        self.assertTrue(accepted)
        self.assertEqual(ledger.divergent_usage_reports, [])

        rejected = ledger.reconcile_self_report(
            source="worker-b",
            reported={"input_tokens": 10},
            metered={"input_tokens": 1000},
        )
        self.assertFalse(rejected)
        self.assertEqual(len(ledger.divergent_usage_reports), 1)
        self.assertEqual(ledger.divergent_usage_reports[0]["source"], "worker-b")

    def test_to_dict_reports_limits_and_spend(self) -> None:
        ledger = BudgetLedger(wall_seconds_limit=5.0, cost_usd_limit=2.0)
        payload = ledger.to_dict()
        self.assertEqual(payload["limits"]["wall_seconds"], 5.0)
        self.assertEqual(payload["limits"]["cost_usd"], 2.0)
        self.assertFalse(payload["exhausted"])


if __name__ == "__main__":
    unittest.main()
