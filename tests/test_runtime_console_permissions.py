import tempfile
import unittest
from pathlib import Path

from matharc.v02.access import InvitationAccessStore
from matharc.v02.access_server import AccessAPI
from matharc.v02.runtime.service import ConsoleRuntimeService, PermissionDeniedError
from matharc.v02.workspace_bundle import write_full_workspace_bundle


class RuntimeConsolePermissionTests(unittest.TestCase):
    def test_cookie_and_topic_scope_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); workspace = root / "workspace"; write_full_workspace_bundle(workspace)
            store = InvitationAccessStore(root / "access")
            issued = store.issue_invitation(email="person@example.com", topic_scopes=["topics"])
            token, _ = store.redeem(email="person@example.com", code=issued.code)
            service = ConsoleRuntimeService(workspace, access_api=AccessAPI(store))
            with self.assertRaises(PermissionDeniedError): service.snapshot("")
            with self.assertRaises(PermissionDeniedError): service.register_action("go", idempotency_key="1", cookie_header=f"matharc_access_session={token}", view="portfolio")


if __name__ == "__main__":
    unittest.main()
