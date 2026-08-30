import unittest

from matharc.frankl_q6 import (
    POSITIVE_CORES,
    classify_two_small_geometries,
    trace_profiles,
    verify_two_small_outside_parts,
)


class FranklQ6TwoSmallTests(unittest.TestCase):
    def test_trace_profiles_match_exact_three_point_enumeration(self) -> None:
        singleton = trace_profiles(1)
        pair = trace_profiles(2)
        self.assertEqual(8, singleton["family_count"])
        self.assertEqual(45, pair["family_count"])
        self.assertEqual(-3, singleton["maximum_deficit"])
        self.assertEqual(-2, pair["maximum_deficit"])
        self.assertEqual(4, singleton["maximum_size"])
        self.assertEqual(7, pair["maximum_size"])

    def test_geometry_orbits_are_complete(self) -> None:
        classification = classify_two_small_geometries()
        self.assertFalse(
            classification["two_singletons"]["possible_with_exactly_two_small_parts"]
        )
        self.assertEqual(4, len(classification["remaining_orbits"]))
        self.assertEqual(42, len(POSITIVE_CORES))

    def test_exact_coarse_minima(self) -> None:
        report = verify_two_small_outside_parts()
        self.assertEqual("PASS", report["status"])
        self.assertEqual(0, report["certified_global_lower_bound_for_subcase"])
        minima = {
            item["geometry"]: item["exact_minimum"] for item in report["results"]
        }
        self.assertEqual(
            {
                "nested_singleton_pair": 0,
                "disjoint_singleton_pair": 0,
                "intersecting_pairs": 6,
                "disjoint_pairs": 6,
            },
            minima,
        )
        self.assertTrue(
            all(item["counterexample_below_minimum"] is None for item in report["results"])
        )


if __name__ == "__main__":
    unittest.main()
