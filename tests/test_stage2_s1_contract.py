from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_s1_contract import validate as validate_s1_contract


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "agents-results/2026-08-31/problem-intelligence-plane"
MACHINE = BUNDLE / ".ssot"
T2_CONTRACT = BUNDLE / "evidence/t2-fixtures/three-real-archives.json"

DOSSIER_IDS = (
    "P-FRANKL-Q6",
    "P-ARXIV-2601-22401-COLLISION",
    "P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS",
)
PAPER_DRY_RUN_COMMAND = (
    "python3 -m unittest -v "
    "tests.test_v02_problem_status.ProblemStatusTests."
    "test_three_paper_dry_run_fixtures_pin_exact_status_facts"
)
RUNTIME_SCOPE = {
    "reserved_nodes": ["T1", "T2"],
    "allowed_operations": ["runtime-replay", "runtime-closure"],
    "s1_boundary": "S1 paper dry-run does not execute or accept T1/T2 runtime work",
}


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain an object")
    return value


class Stage2S1ContractTests(unittest.TestCase):
    def test_project_generator_validation_passes(self) -> None:
        validate_s1_contract(BUNDLE)

    def test_s1_generator_and_machine_contract_pin_the_three_dossier_paper_dry_run(self) -> None:
        planning = _read(MACHINE / "planning-compiler.json")
        s1_specs = [
            node
            for node in planning["nodes"]
            if isinstance(node, dict) and node.get("id") == "S1"
        ]
        self.assertEqual(1, len(s1_specs))
        machine_node = _read(MACHINE / "nodes/S1.json")
        execution_contract = _read(MACHINE / "execution-contracts/S1.json")
        t2_contract = _read(T2_CONTRACT)

        for label, spec in (
            ("planning compiler S1", s1_specs[0]),
            ("machine S1 node", machine_node),
            ("S1 execution contract", execution_contract),
        ):
            with self.subTest(spec=label):
                dry_run = spec.get("pre_acceptance_dry_run")
                self.assertIsInstance(dry_run, dict)
                self.assertEqual(
                    "agents-results/2026-08-31/problem-intelligence-plane/evidence/"
                    "t2-fixtures/three-real-archives.json",
                    dry_run.get("fixture_contract"),
                )
                self.assertEqual(list(DOSSIER_IDS), dry_run.get("dossier_fixture_ids"))
                self.assertEqual(PAPER_DRY_RUN_COMMAND, dry_run.get("command"))
                self.assertEqual("paper-only", dry_run.get("execution_mode"))

        self.assertEqual(
            list(DOSSIER_IDS),
            [case["problem_id"] for case in t2_contract["cases"]],
        )
        self.assertTrue((ROOT / machine_node["pre_acceptance_dry_run"]["fixture_contract"]).is_file())

        for label, spec in (
            ("machine S1 node", machine_node),
            ("S1 execution contract", execution_contract),
        ):
            with self.subTest(scope=label):
                self.assertEqual(RUNTIME_SCOPE, spec.get("runtime_validation_scope"))

        for node_id in ("T1", "T2"):
            with self.subTest(runtime_node=node_id):
                node = _read(MACHINE / f"nodes/{node_id}.json")
                contract = _read(MACHINE / f"execution-contracts/{node_id}.json")
                self.assertNotIn("paper dry-run", " ".join(node["acceptance_commands"]).lower())
                self.assertNotIn("paper dry-run", " ".join(contract["acceptance_commands"]).lower())


if __name__ == "__main__":
    unittest.main()
