from __future__ import annotations

import os
import unittest
import uuid
from pathlib import Path

from matharc.v02.access import (
    InvalidCredentialsError,
    PostgresInvitationAccessStore,
)
from matharc.v02.admin_auth import AdminIdentity
from matharc.v02.admin_service import AdminService


class MutableClock:
    def __init__(self, value: int = 1_900_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


@unittest.skipUnless(
    os.environ.get("MATHARC_TEST_DATABASE_URL"),
    "set MATHARC_TEST_DATABASE_URL to run PostgreSQL integration tests",
)
class PostgresInvitationAccessStoreTests(unittest.TestCase):
    def test_admin_issue_is_redeemable_by_public_access_api_store(self) -> None:
        import psycopg

        dsn = os.environ["MATHARC_TEST_DATABASE_URL"]
        schema = f"matharc_access_test_{uuid.uuid4().hex}"
        bootstrap = psycopg.connect(dsn)
        bootstrap.execute(f'CREATE SCHEMA "{schema}"')
        bootstrap.commit()

        def factory():
            connection = psycopg.connect(dsn)
            connection.execute(f'SET search_path TO "{schema}"')
            return connection

        try:
            migration = (Path(__file__).resolve().parents[1] / "migrations" / "001_admin_access.sql").read_text(encoding="utf-8")
            connection = factory()
            for statement in migration.split(";"):
                if statement.strip():
                    connection.execute(statement)
            connection.commit()
            connection.close()

            clock = MutableClock()
            admin = AdminService(factory, clock=clock)
            admin.ensure_schema()
            identity = AdminIdentity(
                subject="admin-1",
                email="admin@example.edu",
                role="access_admin",
                auth_method="test-proxy",
            )
            grant = admin.issue_invitation(
                identity,
                email="researcher@example.edu",
                topic_scopes=("ramsey-numbers",),
                ttl_seconds=600,
                idempotency_key="issue-1",
            )

            public = PostgresInvitationAccessStore(factory, clock=clock, session_ttl_seconds=120)
            token, session = public.redeem(email="researcher@example.edu", code=grant.code)
            self.assertEqual(("ramsey-numbers",), session.topic_scopes)
            self.assertEqual(session, public.authenticate(token))

            public.logout(token)
            with self.assertRaises(InvalidCredentialsError):
                public.authenticate(token)

            connection = factory()
            row = connection.execute(
                "SELECT redeemed_at FROM invitations WHERE invitation_id=%s",
                (grant.invitation_id,),
            ).fetchone()
            self.assertEqual(clock.value, row[0])
            self.assertEqual(
                1,
                connection.execute("SELECT count(*) FROM access_sessions").fetchone()[0],
            )
            connection.close()
        finally:
            bootstrap.execute(f'DROP SCHEMA "{schema}" CASCADE')
            bootstrap.commit()
            bootstrap.close()


if __name__ == "__main__":
    unittest.main()
