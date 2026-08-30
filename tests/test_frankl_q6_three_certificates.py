import json
import unittest
from pathlib import Path


class FranklQ6ThreeCertificateTests(unittest.TestCase):
    def test_python_and_cpp_certificates_agree(self) -> None:
        root = Path(__file__).resolve().parents[1]
        certificate_dir = root / "benchmarks" / "certificates"
        python_certificate = json.loads(
            (certificate_dir / "frankl-q6-three-small-python.json").read_text(
                encoding="utf-8"
            )
        )
        cpp_certificate = json.loads(
            (certificate_dir / "frankl-q6-three-small-cpp.json").read_text(
                encoding="utf-8"
            )
        )
        expected = [0, 6, 6, 6, 6, 6, 6, 6, 6, 6, 24]
        self.assertEqual("PASS", python_certificate["status"])
        self.assertEqual("PASS", cpp_certificate["status"])
        self.assertEqual(11, python_certificate["orbit_count"])
        self.assertEqual(11, cpp_certificate["orbit_count"])
        self.assertEqual(expected, python_certificate["exact_minima"])
        self.assertEqual(expected, cpp_certificate["exact_minima"])
        self.assertTrue(
            all(
                item["counterexample_below_minimum"] is None
                for item in python_certificate["results"]
            )
        )
        self.assertTrue(
            all(
                item["counterexample_below_minimum"] is None
                for item in cpp_certificate["results"]
            )
        )


if __name__ == "__main__":
    unittest.main()
