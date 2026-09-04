import unittest

from matharc.v02.runtime.view_model import redact_payload


class RuntimeConsoleRedactionTests(unittest.TestCase):
    def test_nested_operational_fields_are_redacted(self):
        value = redact_payload({"a": [{"command": ["python", "--token", "secret"], "env": {"KEY": "value"}, "stack": "trace"}]})
        self.assertEqual(value["a"][0]["command"], "[REDACTED]")
        self.assertEqual(value["a"][0]["env"], "[REDACTED]")
        self.assertEqual(value["a"][0]["stack"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
