import unittest
from matharc.v02.runtime.synthesis import *

class CounterexampleReviewTests(unittest.TestCase):
    def test_pending_review_has_no_trace_authority(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}}, candidate_kind="counterexample")
        q = CounterexampleReviewQueue(); item = q.submit(c)
        self.assertEqual(item.status, "PENDING"); self.assertEqual(len(q.pending()), 1)

    def test_review_requires_rationale_and_cannot_be_resolved_twice(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}}, candidate_kind="counterexample")
        q = CounterexampleReviewQueue(); item = q.submit(c)
        with self.assertRaises(SynthesisError):
            q.resolve(item.review_id, accepted=True, reviewer="", rationale="")
        q.resolve(item.review_id, accepted=True, reviewer="researcher", rationale="replayed independently")
        with self.assertRaises(SynthesisError):
            q.resolve(item.review_id, accepted=False, reviewer="researcher", rationale="conflicting")

    def test_invalid_status_and_non_boolean_decision_fail_closed(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}}, candidate_kind="counterexample")
        with self.assertRaises(SynthesisError):
            CounterexampleReview("review-x", c, status="UNKNOWN")
        q = CounterexampleReviewQueue(); item = q.submit(c)
        with self.assertRaises(SynthesisError):
            q.resolve(item.review_id, accepted=1, reviewer="researcher", rationale="r")

if __name__ == "__main__": unittest.main()
