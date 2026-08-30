import unittest

from matharc.codex_runtime import AGENT_OUTPUT_SCHEMA, build_agent_prompt
from matharc.dashboard import render_dashboard
from matharc.demo import build_demo_run
from matharc.metrics import compute_metrics


class CodexDashboardTests(unittest.TestCase):
    def test_dashboard_contains_live_agent_workspace(self) -> None:
        run = build_demo_run()
        html = render_dashboard(run, compute_metrics(run))
        self.assertIn("MathArc Research", html)
        self.assertIn("Codex Research Agents", html)
        self.assertIn("/api/agent/stream", html)
        self.assertIn("workspace-write", html)
        self.assertIn("Claim / Obligation DAG", html)
        self.assertIn("公开结构化研究轨迹", html)
        self.assertIn("Codex acceptance authority", html)

    def test_prompt_freezes_scope_and_denies_self_acceptance(self) -> None:
        run = build_demo_run()
        prompt = build_agent_prompt(run, "falsifier", "Find the cheapest failure test.")
        self.assertIn(run.contract.statement, prompt)
        self.assertIn("may not self-assign VERIFIED", prompt)
        self.assertIn("Never lift finite", prompt)
        self.assertIn("COUNTEREXAMPLE", prompt)
        self.assertIn("private token-level chain-of-thought", prompt)

    def test_structured_schema_has_no_verified_status(self) -> None:
        statuses = AGENT_OUTPUT_SCHEMA["properties"]["status"]["enum"]
        self.assertNotIn("verified", statuses)
        self.assertNotIn("accepted", statuses)
        self.assertIn("claim_boundary", AGENT_OUTPUT_SCHEMA["required"])


if __name__ == "__main__":
    unittest.main()
