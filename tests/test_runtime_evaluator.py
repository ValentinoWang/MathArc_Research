import unittest

from matharc.v02.runtime.evaluator import (
    EvaluationBudget, EvaluationContract, EvaluationRequest, EvaluationStatus,
)


class RuntimeEvaluatorTests(unittest.TestCase):
    def test_contract_is_seeded_and_budgeted(self):
        req = EvaluationRequest("task", "eval", {"x": 1}, seed=7,
                                budget=EvaluationBudget(max_steps=2))
        result = EvaluationContract("eval", lambda request: {"score": request.seed, "steps": 1}).evaluate(req)
        self.assertEqual(result.status, EvaluationStatus.PASS)
        self.assertEqual(result.seed, 7)
        self.assertEqual(result.budget_digest, req.budget.digest)

    def test_failed_smoke_does_not_start_full_research(self):
        calls = []
        contract = EvaluationContract("eval", lambda request: (_ for _ in ()).throw(ValueError("bad smoke")))
        smoke = contract.smoke_test(EvaluationRequest("task", "eval", seed=1, smoke=True))
        self.assertEqual(smoke.status, EvaluationStatus.FAIL)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
