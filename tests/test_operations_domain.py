from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from matharc.operations import Account, CreditDirection, CreditEntry, OperationsDomainError, OperationsDomainStore, SeatAllocation, UpstreamConfiguration
from matharc.v02.workspace_bundle import write_full_workspace_bundle


class OperationsDomainTests(unittest.TestCase):
    def test_domain_is_research_independent_and_preserves_invariants(self) -> None:
        spec = importlib.util.find_spec("matharc.operations.domain")
        self.assertIsNotNone(spec); source = Path(spec.origin).read_text(encoding="utf-8")
        self.assertNotIn("matharc.v02", source)
        with tempfile.TemporaryDirectory() as directory:
            store = OperationsDomainStore(Path(directory) / "operations")
            account = store.create_account(Account("A", "Research account")); self.assertEqual(store.create_account(account), account)
            store.record_credit(CreditEntry("G-1", "A", CreditDirection.GRANT, 10, "initial grant"))
            store.record_credit(CreditEntry("D-1", "A", CreditDirection.DEBIT, 4, "usage"))
            store.allocate_seat(SeatAllocation("S-1", "A", 2)); store.configure_upstream(UpstreamConfiguration("U-1", "Opaque routing metadata", {"region": "local", "documentation_url": "https://example.test/docs"}))
            snapshot = OperationsDomainStore(Path(directory) / "operations").snapshot()
            self.assertEqual(snapshot["credit_balances"], {"A": 6}); self.assertEqual(snapshot["external_identity"], "not_configured"); self.assertEqual(snapshot["external_payment"], "not_configured")
            raw = json.loads((Path(directory) / "operations" / "operations-domain.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["state_digest_sha256"], raw["state_digest_sha256"])

    def test_rejects_underflow_unknown_accounts_credentials_and_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "operations"; store = OperationsDomainStore(root); store.create_account(Account("A", "A"))
            with self.assertRaises(OperationsDomainError): store.record_credit(CreditEntry("D", "A", CreditDirection.DEBIT, 1, "underflow"))
            with self.assertRaises(OperationsDomainError): store.allocate_seat(SeatAllocation("S", "missing", 1))
            with self.assertRaises(OperationsDomainError): UpstreamConfiguration("U", "provider", {"api_key": "forbidden"})
            with self.assertRaises(OperationsDomainError): UpstreamConfiguration("U-url", "provider", {"documentation_url": "https://user:password@example.test/docs"})
            with self.assertRaises(OperationsDomainError): UpstreamConfiguration("U-query", "provider", {"documentation_url": "https://example.test/docs?api_key=forbidden"})
            with self.assertRaises(OperationsDomainError): UpstreamConfiguration("U-field", "provider", {"endpoint": "https://example.test"})
            store.record_credit(CreditEntry("G", "A", CreditDirection.GRANT, 1, "grant"))
            data = json.loads((root / "operations-domain.json").read_text(encoding="utf-8")); data["credits"][0]["amount"] = 99; (root / "operations-domain.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(OperationsDomainError): store.snapshot()

    def test_rejects_an_operations_root_inside_a_research_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            write_full_workspace_bundle(workspace)
            with self.assertRaises(OperationsDomainError):
                OperationsDomainStore(workspace / "operations")


if __name__ == "__main__": unittest.main()
