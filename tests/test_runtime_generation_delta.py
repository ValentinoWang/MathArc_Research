from __future__ import annotations

import unittest

from matharc.v02.runtime.research_director.agenda import compile_next_generation_agenda


class RuntimeGenerationDeltaTests(unittest.TestCase):
    def test_second_generation_route_is_explainably_changed_by_first_failure(self) -> None:
        first_failure = {
            "failure_id": "cand-g1",
            "failure_class": "FINITE_TO_GLOBAL",
            "repair": "attack the infinite-volume bridge independently",
        }
        next_agenda = compile_next_generation_agenda(
            generation_id="g2",
            parent_generation_id="g1",
            failures=(first_failure,),
            route_changes=({"route_id": "route-g1-to-bridge-attack", "action": "bridge attack"},),
        )

        self.assertEqual(next_agenda.parent_generation_id, "g1")
        self.assertIn("cand-g1", next_agenda.consumed_fact_ids)
        self.assertIn("route-g1-to-bridge-attack", next_agenda.consumed_fact_ids)
        self.assertTrue(any("infinite-volume bridge" in item.action for item in next_agenda.items))
        self.assertTrue(any("bridge attack" in item.action for item in next_agenda.items))
        self.assertTrue(all("g1" in item.rationale for item in next_agenda.items))


if __name__ == "__main__":
    unittest.main()
