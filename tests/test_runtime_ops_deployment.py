from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RuntimeOpsDeploymentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = (ROOT / "deploy/matharc-research.service").read_text(encoding="utf-8")
        self.env = (ROOT / "deploy/matharc-research.env.example").read_text(encoding="utf-8")

    def test_systemd_persistent_hardened_service(self) -> None:
        for token in ("Type=simple", "User=matharc", "Restart=on-failure", "TimeoutStartSec=30s", "TimeoutStopSec=30s", "StateDirectory=matharc-research", "EnvironmentFile=/etc/matharc-research/matharc-research.env", "LoadCredential=api-token:", "ProtectSystem=strict", "NoNewPrivileges=true"):
            self.assertIn(token, self.service)
        self.assertNotIn("/tmp/", self.service)

    def test_env_has_external_secret_and_release_identity_inputs(self) -> None:
        for token in ("MATHARC_RUNTIME_RUN_ID=", "MATHARC_RELEASE_ID=", "MATHARC_RUN_PATH=/var/lib/matharc-research/", "MATHARC_BACKUP_PATH=/var/lib/matharc-research/", "external", "secret"):
            self.assertIn(token, self.env)
        self.assertNotIn("API_KEY=", self.env)


if __name__ == "__main__":
    unittest.main()
