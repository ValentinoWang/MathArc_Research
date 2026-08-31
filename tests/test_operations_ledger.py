from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from matharc.operations import OperationsLedger, OperationsLedgerError


class OperationsLedgerTests(unittest.TestCase):
    def test_operations_never_mutate_research_input(self) -> None:
        replay = b'{"research":"frozen"}'
        digest = hashlib.sha256(replay).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            ledger = OperationsLedger(Path(directory) / "operations.json", digest)
            ledger.append(record_id="A", kind="ACCOUNT_CREATED", payload={"account":"u"})
            ledger.append(record_id="U", kind="UPSTREAM_CONFIGURED", payload={"model":"local"})
            self.assertEqual(replay, b'{"research":"frozen"}')
            self.assertEqual(ledger.snapshot()["research_replay_digest"], digest)
            with self.assertRaises(OperationsLedgerError):
                ledger.append(record_id="A", kind="ACCOUNT_CREATED", payload={})

    def test_negative_metered_values_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OperationsLedger(Path(directory) / "operations.json", "a" * 64)
            with self.assertRaises(OperationsLedgerError):
                ledger.append(record_id="B", kind="BALANCE_CREDITED", payload={"amount": -1})

    def test_tampered_history_is_rejected_when_reopened(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "operations.json"
            ledger = OperationsLedger(path, "a" * 64)
            ledger.append(record_id="A", kind="ACCOUNT_CREATED", payload={"account":"u"})
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["records"][0]["payload"]["account"] = "tampered"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(OperationsLedgerError):
                OperationsLedger(path, "a" * 64)

    def test_records_are_deep_copies_of_the_append_only_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "operations.json"
            ledger = OperationsLedger(path, "a" * 64)
            ledger.append(record_id="A", kind="ACCOUNT_CREATED", payload={"account": "u"})
            exposed = ledger.records[0]
            exposed["payload"]["account"] = "tampered"
            ledger.append(record_id="B", kind="SEAT_SET", payload={"seats": 2})
            reopened = OperationsLedger(path, "a" * 64)
            self.assertEqual(reopened.records[0]["payload"]["account"], "u")

    def test_append_result_cannot_mutate_the_append_only_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "operations.json"
            ledger = OperationsLedger(path, "a" * 64)
            created = ledger.append(
                record_id="A", kind="ACCOUNT_CREATED", payload={"account": "u"}
            )
            created["payload"]["account"] = "tampered"
            ledger.append(record_id="B", kind="SEAT_SET", payload={"seats": 2})
            reopened = OperationsLedger(path, "a" * 64)
            self.assertEqual(reopened.records[0]["payload"]["account"], "u")


if __name__ == "__main__":
    unittest.main()
