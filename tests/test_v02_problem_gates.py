from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from matharc.v02.local_store import LocalStoreError
from matharc.v02.problem_gates import CandidateProblem, GATE_IDS, GateEvidence, GateVerdict, ProblemGateStore, ProblemStatementVersion, ResultGraph, ResultGraphEdge, ResultRelation
from matharc.v02.workspace_bundle import write_full_workspace_bundle


def gates(verdict: GateVerdict = GateVerdict.PASSED) -> tuple[GateEvidence, ...]:
    return tuple(GateEvidence(gate_id, verdict, f"EV-{index}", "2026-09-01T00:00:00+00:00") for index, gate_id in enumerate(GATE_IDS, 1))


class ProblemGatesTests(unittest.TestCase):
    def test_nine_gates_and_ready_derivation(self) -> None:
        statement = ProblemStatementVersion("P-1", 1, "A bounded statement")
        candidate = CandidateProblem("P-1", statement.statement_version_id, gates())
        self.assertTrue(candidate.ready_to_start)
        blocked = CandidateProblem("P-1", statement.statement_version_id, gates(GateVerdict.PENDING))
        self.assertFalse(blocked.ready_to_start)
        with self.assertRaises(LocalStoreError): CandidateProblem("P", "P@1", gates()[:-1])

    def test_persistence_graph_integrity_and_tamper_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "problems"; store = ProblemGateStore(root)
            first = ProblemStatementVersion("P-1", 1, "first"); second = ProblemStatementVersion("P-2", 1, "second")
            graph = ResultGraph(tuple(sorted((first.statement_version_id, second.statement_version_id))), (ResultGraphEdge("E-1", first.statement_version_id, second.statement_version_id, ResultRelation.DERIVES_FROM, "EV-graph"),))
            store.replace(tuple(sorted((first, second), key=lambda item: item.statement_version_id)), (CandidateProblem("P-1", first.statement_version_id, gates()),), graph)
            self.assertEqual(store.load()[0][0], first)
            data = json.loads((root / "candidate-problems.json").read_text(encoding="utf-8")); data["candidates"][0]["ready_to_start"] = False
            (root / "candidate-problems.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(LocalStoreError): store.load()

    def test_rejects_cycles_and_workspace_store(self) -> None:
        with self.assertRaises(LocalStoreError):
            ResultGraph(("A", "B"), (ResultGraphEdge("E1", "A", "B", ResultRelation.DERIVES_FROM, "x"), ResultGraphEdge("E2", "B", "A", ResultRelation.DERIVES_FROM, "x")))
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"; write_full_workspace_bundle(workspace)
            with self.assertRaises(LocalStoreError): ProblemGateStore(workspace / "problems")


if __name__ == "__main__": unittest.main()
