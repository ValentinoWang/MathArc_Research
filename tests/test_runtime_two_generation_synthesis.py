from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from matharc.v02.runtime.contracts import ExecutionStatus, ResearchWorkerSpec, WorkerExecutionResult
from matharc.v02.runtime.generation import GenerationInputSnapshot
from matharc.v02.runtime.reducer import GenerationReducer
from matharc.v02.runtime.run_store import RuntimeStore


class RuntimeTwoGenerationSynthesisTests(unittest.TestCase):
    def _snapshot(self, generation_id: str, source_payload: object) -> GenerationInputSnapshot:
        worker = ResearchWorkerSpec("researcher", backend="deterministic-test")
        return GenerationInputSnapshot.from_inputs(
            workspace_id="workspace",
            trace_id="trace",
            runtime_run_id="run-two-generations",
            generation_id=generation_id,
            trace={"claim": "finite family"},
            contract={"version": 1},
            agenda={"generation": generation_id},
            worker_specs=(worker,),
            tool_registry={"deterministic-test": "v1"},
            source_payload=source_payload,
        )

    def test_consecutive_generations_commit_and_persist_separately(self) -> None:
        first = GenerationReducer(self._snapshot("g1", {"route": "enumerate"}))
        first_result = WorkerExecutionResult(
            "workspace", "trace", "run-two-generations", "g1", "researcher", "exec-g1",
            ExecutionStatus.SUCCEEDED, "digest-g1", candidate_ids=("cand-g1",),
        )
        first_commit = first.commit([first_result])

        second = GenerationReducer(self._snapshot("g2", {"route": "attack", "parent": first_commit.commit_digest}))
        second_result = WorkerExecutionResult(
            "workspace", "trace", "run-two-generations", "g2", "researcher", "exec-g2",
            ExecutionStatus.SUCCEEDED, "digest-g2", candidate_ids=("cand-g2",),
        )
        second_commit = second.commit([second_result])

        self.assertNotEqual(first_commit.generation_id, second_commit.generation_id)
        self.assertNotEqual(first_commit.commit_digest, second_commit.commit_digest)
        self.assertEqual(first_commit.results[0].candidate_ids, ("cand-g1",))
        self.assertEqual(second_commit.results[0].candidate_ids, ("cand-g2",))

        with tempfile.TemporaryDirectory() as directory:
            store = RuntimeStore(Path(directory) / "runtime")
            store.record_generation_commit(first_commit)
            store.record_generation_commit(second_commit)
            commits = store.state["commits"]
            self.assertEqual([item["generation_id"] for item in commits], ["g1", "g2"])
            self.assertEqual(len(commits), 2)


if __name__ == "__main__":
    unittest.main()
