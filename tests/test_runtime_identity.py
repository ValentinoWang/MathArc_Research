import unittest

from matharc.v02.runtime.identity import IdentityError, RuntimeIdentity, idempotency_key


class RuntimeIdentityTests(unittest.TestCase):
    def test_hierarchy_and_round_trip(self):
        value = RuntimeIdentity("w", "t", "r", "g", "worker", "exec", "candidate", "evidence")
        self.assertEqual(RuntimeIdentity.from_dict(value.to_dict()), value)
        self.assertEqual(idempotency_key("r", "g"), "r+g")

    def test_rejects_gaps_unknown_and_cross_workspace(self):
        with self.assertRaises(IdentityError):
            RuntimeIdentity("w", "t", "r", None, "worker")
        with self.assertRaises(IdentityError):
            RuntimeIdentity.from_dict({"workspace_id": "w", "unexpected": "x"})
        parent = RuntimeIdentity("w", "t", "r")
        with self.assertRaises(IdentityError):
            parent.require_ancestor_of(RuntimeIdentity("other", "t", "r"))


if __name__ == "__main__":
    unittest.main()
