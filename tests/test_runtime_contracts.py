import unittest

from matharc.v02.runtime.contracts import (
    ContractError, ExecutionStatus, ResearchRunSpec, ResearchWorkerSpec,
    RuntimeActionReceipt, ActionStatus, WorkerExecutionResult,
)


class RuntimeContractTests(unittest.TestCase):
    def test_strict_round_trip(self):
        value = ResearchRunSpec("w", "t", "r", "task", workers=(ResearchWorkerSpec("worker"),))
        self.assertEqual(ResearchRunSpec.from_dict(value.to_dict()), value)
        with self.assertRaises(ContractError):
            ResearchRunSpec.from_dict({**value.to_dict(), "extra": 1})

    def test_failure_requires_classification_and_unknown_status_rejected(self):
        with self.assertRaises(ContractError):
            WorkerExecutionResult("w", "t", "r", "g", "worker", "e", ExecutionStatus.FAILED)
        result = WorkerExecutionResult("w", "t", "r", "g", "worker", "e", ExecutionStatus.SUCCEEDED)
        with self.assertRaises(ContractError):
            WorkerExecutionResult.from_dict({**result.to_dict(), "status": "UNKNOWN"})

    def test_action_round_trip(self):
        receipt = RuntimeActionReceipt("a", "start", "principal", "r", ActionStatus.ACCEPTED)
        self.assertEqual(RuntimeActionReceipt.from_dict(receipt.to_dict()), receipt)


if __name__ == "__main__":
    unittest.main()
