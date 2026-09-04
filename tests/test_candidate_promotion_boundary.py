import unittest

from matharc.v02.runtime.contracts import ResearchRunSpec, ResearchWorkerSpec
from matharc.v02.runtime.coordinator import RuntimeCoordinator


class CandidatePromotionBoundaryTests(unittest.TestCase):
    def test_success_only_yields_candidate_envelope(self):
        spec = ResearchRunSpec("w", "t", "run-boundary", "task",
                               workers=(ResearchWorkerSpec("worker", backend="deterministic-test"),))
        result = RuntimeCoordinator().run(spec)
        self.assertEqual(len(result.candidates), 1)
        self.assertFalse(hasattr(result, "promote_claim"))
        self.assertNotEqual(getattr(spec, "status").value, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
