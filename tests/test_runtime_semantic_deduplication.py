import unittest
from matharc.v02.runtime.budget import ResourceLedger, ResourceReceipt, SemanticDeduplicator


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


if __name__ == "__main__":
    unittest.main()
