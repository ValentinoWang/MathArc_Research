import unittest
import tempfile
from pathlib import Path
from matharc.v02.runtime.budget import ResourceLedger, ResourceReceipt, SemanticDeduplicator
from matharc.v02.runtime.run_store import RuntimeStore


class RuntimeSemanticDeduplicationTests(unittest.TestCase):
    def test_same_semantic_experiment_is_claimed_once(self):
        dedup = SemanticDeduplicator()
        self.assertTrue(dedup.claim({"problem": "x", "execution_id": "one"}, execution_id="one"))
        self.assertFalse(dedup.claim({"problem": "x", "execution_id": "two"}, execution_id="two"))

    def test_ledger_uses_receipt_values(self):
        ledger = ResourceLedger(cost_usd_limit=1)
        ledger.record_receipt(ResourceReceipt("e", cost_usd=.4, input_tokens=3))
        ledger.record_receipt(ResourceReceipt("e", cost_usd=9))
        self.assertEqual(ledger.spent_cost_usd, .4)

    def test_receipts_reject_non_finite_values_and_strict_conflicts(self):
        with self.assertRaises(ValueError):
            ResourceReceipt("nan", cost_usd=float("nan"))
        with self.assertRaises(ValueError):
            ResourceReceipt.from_mapping({"execution_id": "fraction", "input_tokens": 1.5})
        ledger = ResourceLedger()
        ledger.record_receipt(ResourceReceipt("same", cost_usd=.1))
        with self.assertRaises(ValueError):
            ledger.validate_receipt(ResourceReceipt("same", cost_usd=.2))

    def test_admission_is_atomic_and_runtime_store_replays_claims_and_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RuntimeStore(Path(directory) / "runtime")
            ledger = ResourceLedger(cost_usd_limit=1, runtime_store=store)
            self.assertTrue(ledger.admit({"max_cost": .6}, execution_id="exec-a"))
            self.assertFalse(ledger.admit({"max_cost": .5}, execution_id="exec-b"))
            ledger.record_receipt(ResourceReceipt("exec-a", cost_usd=.4, semantic_key="key-a"))
            dedup = SemanticDeduplicator(runtime_store=store)
            self.assertTrue(dedup.claim({"problem": "x"}, execution_id="claim-a", snapshot_digest="snap"))
            restarted_store = RuntimeStore.load(Path(directory) / "runtime")
            restored_ledger = ResourceLedger(cost_usd_limit=1, runtime_store=restarted_store)
            restored_dedup = SemanticDeduplicator(runtime_store=restarted_store)
            self.assertEqual(restored_ledger.spent_cost_usd, .4)
            self.assertEqual(restored_dedup.execution_for({"problem": "x"}, snapshot_digest="snap"), "claim-a")


if __name__ == "__main__":
    unittest.main()
