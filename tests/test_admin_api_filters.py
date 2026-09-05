from __future__ import annotations

import unittest

from matharc.v02.admin_auth import AdminAuthError
from matharc.v02.admin_server import AdminAPI
from matharc.v02.admin_service import InvitationRecord

_HEADERS = {
    "X-Admin-Subject": "admin-1",
    "X-Admin-Email": "admin@example.edu",
    "X-Admin-Role": "access_admin",
    "X-Admin-Auth-Method": "proxy",
}


class RecordingAdminService:
    def __init__(self) -> None:
        self.application_list: dict[str, object] | None = None
        self.application_count: dict[str, object] | None = None
        self.invitation_list: dict[str, object] | None = None
        self.invitation_count: dict[str, object] | None = None

    def list_applications(self, identity, **kwargs):
        self.application_list = kwargs
        return [{"application_id": "app-1", "status": "PENDING"}]

    def count_applications(self, identity, **kwargs):
        self.application_count = kwargs
        return 42

    def list_invitations(self, identity, **kwargs):
        self.invitation_list = kwargs
        return [InvitationRecord("inv-1", "person@example.edu", ("topic",), 1, 4_000_000_000, None, None)]

    def count_invitations(self, identity, **kwargs):
        self.invitation_count = kwargs
        return 7

    def issue_invitation(self, identity, **kwargs):
        raise AdminAuthError("role is not allowed")


class AdminAPIFilterTests(unittest.TestCase):
    def test_applications_pass_filters_offset_and_real_total(self) -> None:
        service = RecordingAdminService()
        response = AdminAPI(service, trusted_proxy=True).get(
            "/api/admin/applications",
            _HEADERS,
            {"status": ["PENDING"], "q": ["Alice"], "page": ["3"], "page_size": ["10"]},
        )

        self.assertEqual(200, response.status)
        self.assertEqual(42, response.payload["total"])
        self.assertEqual({"limit": 10, "offset": 20, "status": "PENDING", "search": "Alice"}, service.application_list)
        self.assertEqual({"status": "PENDING", "search": "Alice"}, service.application_count)

    def test_invitations_pass_status_search_pagination_and_total(self) -> None:
        service = RecordingAdminService()
        response = AdminAPI(service, trusted_proxy=True).get(
            "/api/admin/invitations",
            _HEADERS,
            {"status": ["active"], "q": ["person"], "page": ["2"], "page_size": ["5"]},
        )

        self.assertEqual(200, response.status)
        self.assertEqual(7, response.payload["total"])
        self.assertEqual("active", response.payload["items"][0]["status"])
        self.assertEqual({"limit": 5, "offset": 5, "status": "active", "search": "person"}, service.invitation_list)
        self.assertEqual({"status": "active", "search": "person"}, service.invitation_count)

    def test_authenticated_role_denial_returns_forbidden(self) -> None:
        response = AdminAPI(RecordingAdminService(), trusted_proxy=True).post(
            "/api/admin/invitations",
            headers={**_HEADERS, "Idempotency-Key": "role-denied"},
            body=b'{"email":"person@example.edu","topic_scopes":["topic"]}',
        )
        self.assertEqual(403, response.status)


if __name__ == "__main__":
    unittest.main()
