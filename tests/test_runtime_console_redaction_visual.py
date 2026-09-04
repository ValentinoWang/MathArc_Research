import unittest
from pathlib import Path


class RuntimeConsoleRedactionVisualTests(unittest.TestCase):
    def test_live_simulated_write_guard_is_present(self):
        source = (Path(__file__).parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        self.assertIn("LIVE_SIMULATED_WRITES", source)
        self.assertIn('aria-disabled', source)


if __name__ == "__main__":
    unittest.main()
