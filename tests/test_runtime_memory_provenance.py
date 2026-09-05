import unittest
from matharc.v02.episode_memory import EpisodeMemory
from matharc.v02.runtime.episode_memory import RuntimeEpisodeMemory
from matharc.v02.schema import FailureClass
from matharc.v02.runtime.synthesis import synthesize_candidate

class RuntimeMemoryProvenanceTests(unittest.TestCase):
    def test_distilled_episode_keeps_runtime_identity(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}})
        e = EpisodeMemory().ingest_candidate(c)
        self.assertTrue(e.has_runtime_provenance)

    def test_failure_lesson_keeps_run_generation_candidate_origin(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}})
        lesson = RuntimeEpisodeMemory().distill_failure(c, failure_class=FailureClass.UNKNOWN,
            trigger="trigger", diagnosis="diagnosis", repair="repair")
        self.assertEqual((lesson.source_run_id, lesson.generation_id, lesson.candidate_id,
                          lesson.candidate_origin), ("r", "g", c.candidate_id, "runtime-execution"))

if __name__ == "__main__": unittest.main()
