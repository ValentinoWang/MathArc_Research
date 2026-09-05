import unittest
from unittest.mock import patch

from matharc.v02.runtime.contracts import ResearchRunSpec, ResearchWorkerSpec
from matharc.v02.runtime.coordinator import RuntimeCoordinator
from matharc.v02.trace import ResearchTrace


class CandidatePromotionBoundaryTests(unittest.TestCase):
    def test_success_only_yields_candidate_envelope(self):
        spec = ResearchRunSpec("w", "t", "run-boundary", "task",
                               workers=(ResearchWorkerSpec("worker", backend="deterministic-test"),))
        with patch.object(ResearchTrace, "promote_claim", side_effect=AssertionError("runtime promotion")) as promote:
            result = RuntimeCoordinator().run(spec)
        self.assertEqual(len(result.candidates), 1)
        self.assertFalse(hasattr(result, "promote_claim"))
        self.assertNotEqual(getattr(spec, "status").value, "COMPLETED")
        self.assertFalse(promote.called)


if __name__ == "__main__":
    unittest.main()
