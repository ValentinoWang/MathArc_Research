from __future__ import annotations

import unittest

from matharc.v02.schema import TheoremContract
from matharc.v02.trace import ResearchTrace, TraceValidationError, runtime_health


class RuntimeAuthorityBoundaryTests(unittest.TestCase):
    def test_health_snapshot_cannot_mark_a_claim_proved(self) -> None:
        trace = ResearchTrace("trace-1", TheoremContract("K", "p", (), "s"))
        health = runtime_health(trace, runtime_run_id="runtime-1")
        self.assertNotIn("PROVED", health)
        self.assertEqual(trace.claims, {})

    def test_runtime_status_api_rejects_proved(self) -> None:
        trace = ResearchTrace("trace-1", TheoremContract("K", "p", (), "s"))
        with self.assertRaises(TraceValidationError):
            trace.record_runtime_status("PROVED")


if __name__ == "__main__":
    unittest.main()
