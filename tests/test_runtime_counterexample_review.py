import unittest
from matharc.v02.runtime.synthesis import *

class CounterexampleReviewTests(unittest.TestCase):
    def test_pending_review_has_no_trace_authority(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}}, candidate_kind="counterexample")
        q = CounterexampleReviewQueue(); item = q.submit(c)
        self.assertEqual(item.status, "PENDING"); self.assertEqual(len(q.pending()), 1)

if __name__ == "__main__": unittest.main()
