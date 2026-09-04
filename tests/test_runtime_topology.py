import unittest

from matharc.v02.runtime.topology import ResearchMember, TopologyValidationError, compile_topology


class RuntimeTopologyTests(unittest.TestCase):
    def test_compiles_mechanism_budget_objective_and_isolated_scope(self):
        topology = compile_topology("route-a", [{"id": "a", "role": "prover", "mechanism": "symbolic", "budget": {"cost_usd": 1}, "objective": "find proof", "write_scope": ["runs/a"]}])
        self.assertEqual(topology.members[0].mechanism, "symbolic")
        self.assertTrue(topology.topology_digest_sha256)

    def test_rejects_missing_contract_fields_and_overlap(self):
        with self.assertRaises(TopologyValidationError):
            compile_topology("route", [{"id": "a", "role": "r", "mechanism": "m", "budget": {}, "objective": "o", "write_scope": []}])
        with self.assertRaises(TopologyValidationError):
            compile_topology("route", [{"id": "a", "role": "r", "mechanism": "m", "budget": {"x": 1}, "objective": "o", "write_scope": ["same"]}, {"id": "b", "role": "r", "mechanism": "m", "budget": {"x": 1}, "objective": "o", "write_scope": ["same"]}])


if __name__ == "__main__":
    unittest.main()
