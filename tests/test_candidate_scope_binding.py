import unittest
from matharc.v02.runtime.synthesis import synthesize_candidate
from matharc.v02.runtime.verification import bind_candidate_scope, ScopeBindingError

class CandidateScopeBindingTests(unittest.TestCase):
    def test_scope_mismatch_rejected(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{"scope":"finite"}}, claim_ids=("C",))
        with self.assertRaises(ScopeBindingError): bind_candidate_scope(c, claim_id="C", proposition="P", quantifier="forall", scope="global")

    def test_missing_scope_fields_and_claim_association_are_rejected(self):
        missing = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}}, claim_ids=("C",))
        with self.assertRaises(ScopeBindingError):
            bind_candidate_scope(missing, claim_id="C", proposition="P", quantifier="forall", scope="global")
        complete = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{"proposition":"P","quantifier":"forall","scope":"global"}})
        with self.assertRaises(ScopeBindingError):
            bind_candidate_scope(complete, claim_id="C", proposition="P", quantifier="forall", scope="global")

if __name__ == "__main__": unittest.main()
