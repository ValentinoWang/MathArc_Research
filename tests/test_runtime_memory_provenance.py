import unittest
from matharc.v02.episode_memory import EpisodeMemory
from matharc.v02.runtime.synthesis import synthesize_candidate

class RuntimeMemoryProvenanceTests(unittest.TestCase):
    def test_distilled_episode_keeps_runtime_identity(self):
        c = synthesize_candidate({"workspace_id":"w","trace_id":"t","runtime_run_id":"r","generation_id":"g","payload":{}})
        e = EpisodeMemory().ingest_candidate(c)
        self.assertTrue(e.has_runtime_provenance)

if __name__ == "__main__": unittest.main()
