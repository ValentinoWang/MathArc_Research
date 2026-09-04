import unittest
from matharc.v02.runtime.research_director.agenda import compile_next_generation_agenda

class NextGenerationAgendaTests(unittest.TestCase):
    def test_items_reference_prior_facts(self):
        a = compile_next_generation_agenda(generation_id="g2", parent_generation_id="g1", failures=[{"failure_id":"f1","repair":"bound scope"}], episodes=[{"episode_id":"e1"}], review_gaps=[{"event_id":"q1"}], route_changes=[{"route_id":"r1"}])
        self.assertTrue(a.items); self.assertTrue(all(i.source_fact_ids for i in a.items))
        self.assertIn("f1", a.consumed_fact_ids)

if __name__ == "__main__": unittest.main()
