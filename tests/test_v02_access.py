from __future__ import annotations

import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from matharc.v02.access import (
    AccessConflictError,
    AccessStateError,
    AccessValidationError,
    InvalidCredentialsError,
    InvitationAccessStore,
)


class MutableClock:
    def __init__(self, value: int = 1_800_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


class InvitationAccessStoreTests(unittest.TestCase):
    def store(
        self,
        root: str | Path,
        *,
        clock: MutableClock | None = None,
        session_ttl_seconds: int = 3_600,
    ) -> InvitationAccessStore:
        return InvitationAccessStore(
            root,
            clock=clock or MutableClock(),
            session_ttl_seconds=session_ttl_seconds,
        )

    def test_application_has_strict_public_pending_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            application = self.store(directory).submit_application(
                email=" Researcher@Example.EDU ",
                institution="Example University",
                research_role="Postdoctoral researcher",
                research_direction="Extremal combinatorics",
                purpose="Evaluate a private topic workspace with collaborators.",
            )

            self.assertEqual(
                {
                    "application_id",
                    "status",
                    "email",
                    "submitted_at",
                },
                set(application.to_dict()),
            )
            self.assertEqual("PENDING", application.status)
            self.assertEqual("researcher@example.edu", application.email)

            state = json.loads((Path(directory) / "access-state.json").read_text())
            persisted = state["applications"][0]
            self.assertEqual("Example University", persisted["institution"])
            self.assertEqual("Postdoctoral researcher", persisted["research_role"])
            self.assertEqual("Extremal combinatorics", persisted["research_direction"])
            self.assertIn("private topic workspace", persisted["purpose"])

    def test_application_validation_is_strict_and_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(directory)
            before = (Path(directory) / "access-state.json").read_bytes()
            invalid = (
                {"email": "not-an-email"},
                {"institution": " "},
                {"research_role": ""},
                {"research_direction": "x" * 501},
                {"purpose": "\x00invalid"},
            )
            base = {
                "email": "person@example.edu",
                "institution": "Example University",
                "research_role": "Researcher",
                "research_direction": "Combinatorics",
                "purpose": "Evaluate the preview.",
            }
            for replacement in invalid:
                with self.subTest(replacement=replacement):
                    values = {**base, **replacement}
                    with self.assertRaises(AccessValidationError):
                        store.submit_application(**values)
            self.assertEqual(before, (Path(directory) / "access-state.json").read_bytes())

    def test_invitation_is_email_bound_single_use_scoped_and_secret_free_at_rest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(directory)
            issued = store.issue_invitation(
                email="Researcher@Example.edu",
                topic_scopes=("ramsey-numbers", "erdos-szekeres"),
                ttl_seconds=600,
            )
            self.assertGreaterEqual(len(issued.code), 40)
            disk_after_issue = (Path(directory) / "access-state.json").read_text()
            self.assertNotIn(issued.code, disk_after_issue)
            self.assertNotIn("code\"", disk_after_issue)
            self.assertEqual(
                ("ramsey-numbers", "erdos-szekeres"),
                issued.invitation.topic_scopes,
            )

            with self.assertRaises(InvalidCredentialsError):
                store.redeem(email="other@example.edu", code=issued.code)

            token, session = store.redeem(
                email="researcher@example.edu",
                code=issued.code,
            )
            self.assertGreaterEqual(len(token), 40)
            self.assertEqual(
                {
                    "email": "researcher@example.edu",
                    "topic_scopes": ["ramsey-numbers", "erdos-szekeres"],
                    "expires_at": 1_800_003_600,
                },
                session.to_dict(),
            )
            disk_after_redeem = (Path(directory) / "access-state.json").read_text()
            self.assertNotIn(issued.code, disk_after_redeem)
            self.assertNotIn(token, disk_after_redeem)
            self.assertIn("code_hash_sha256", disk_after_redeem)
            self.assertIn("token_hash_sha256", disk_after_redeem)

            with self.assertRaises(InvalidCredentialsError):
                store.redeem(email="researcher@example.edu", code=issued.code)

    def test_expired_or_revoked_invitation_cannot_be_redeemed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clock = MutableClock()
            store = self.store(directory, clock=clock)
            expired = store.issue_invitation(
                email="expired@example.edu",
                topic_scopes=("topic-a",),
                ttl_seconds=10,
            )
            clock.value += 10
            with self.assertRaises(InvalidCredentialsError):
                store.redeem(email="expired@example.edu", code=expired.code)

            active = store.issue_invitation(
                email="revoked@example.edu",
                topic_scopes=("topic-b",),
            )
            revoked = store.revoke_invitation(active.invitation.invitation_id)
            self.assertEqual(clock.value, revoked.revoked_at)
            with self.assertRaises(InvalidCredentialsError):
                store.redeem(email="revoked@example.edu", code=active.code)
            with self.assertRaises(AccessConflictError):
                store.revoke_invitation(active.invitation.invitation_id)

    def test_session_authentication_expiration_and_logout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clock = MutableClock()
            store = self.store(directory, clock=clock, session_ttl_seconds=20)
            issued = store.issue_invitation(
                email="person@example.edu",
                topic_scopes=("topic-a",),
            )
            token, expected = store.redeem(email="person@example.edu", code=issued.code)
            self.assertEqual(expected, store.authenticate(token))
            with self.assertRaises(InvalidCredentialsError):
                store.authenticate("not-a-real-session-token")

            store.logout(token)
            with self.assertRaises(InvalidCredentialsError):
                store.authenticate(token)
            with self.assertRaises(InvalidCredentialsError):
                store.logout(token)

            second = store.issue_invitation(
                email="person@example.edu",
                topic_scopes=("topic-b",),
            )
            second_token, _ = store.redeem(
                email="person@example.edu",
                code=second.code,
            )
            clock.value += 20
            with self.assertRaises(InvalidCredentialsError):
                store.authenticate(second_token)

    def test_unknown_fields_bad_digest_and_cross_record_tampering_fail_closed(self) -> None:
        def rewrite(path: Path, mutation) -> None:
            value = json.loads(path.read_text())
            mutation(value)
            path.write_text(json.dumps(value), encoding="utf-8")

        mutations = (
            lambda value: value.__setitem__("unexpected", True),
            lambda value: value.__setitem__("state_digest_sha256", "0" * 64),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "access-state.json"
                self.store(directory)
                rewrite(path, mutation)
                with self.assertRaises(AccessStateError):
                    self.store(directory)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "access-state.json"
            store = self.store(directory)
            issued = store.issue_invitation(
                email="person@example.edu",
                topic_scopes=("topic-a",),
            )
            token, _ = store.redeem(email="person@example.edu", code=issued.code)
            value = json.loads(path.read_text())
            value["sessions"][0]["email"] = "attacker@example.edu"
            # Even a recomputed public digest cannot bypass cross-record invariants.
            from matharc.v02.local_store import state_digest

            value["state_digest_sha256"] = state_digest(value)
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(AccessStateError):
                self.store(directory)
            with self.assertRaises(AccessStateError):
                store.authenticate(token)

    def test_rejects_research_workspace_root_or_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "workspace.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(AccessStateError):
                self.store(root / "private-access")

    def test_concurrent_issuance_is_locked_without_lost_updates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(directory)
            barrier = threading.Barrier(8)

            def issue(index: int) -> str:
                barrier.wait()
                return store.issue_invitation(
                    email=f"person-{index}@example.edu",
                    topic_scopes=(f"topic-{index}",),
                ).invitation.invitation_id

            with ThreadPoolExecutor(max_workers=8) as executor:
                identifiers = list(executor.map(issue, range(8)))

            self.assertEqual(8, len(set(identifiers)))
            state = json.loads((Path(directory) / "access-state.json").read_text())
            self.assertEqual(8, len(state["invitations"]))


if __name__ == "__main__":
    unittest.main()
