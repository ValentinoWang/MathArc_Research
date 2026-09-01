from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError

from matharc.v02.literature import (
    AdapterReport,
    ImportDisposition,
    LiteratureAdapter,
    Provider,
    TransportResponse,
)
from matharc.v02.literature_base import LiteratureBase
from matharc.v02.source_observation import LicenseStatus, ObservationStatus


CONTENT = b"bounded literature bytes"
FIXED_TIME = "2026-09-01T00:00:00+00:00"


class FakeTransport:
    def __init__(self, *responses: TransportResponse | BaseException) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout: float) -> TransportResponse:
        self.calls.append((url, timeout))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def record(
    *,
    provider: str = "arXiv",
    identity: str = "2601.22401",
    version: str | None = "v1",
    license_status: str = "OPEN",
    summary: str = "The record describes a research question and its source metadata.",
    content: bytes = CONTENT,
) -> dict[str, object]:
    value: dict[str, object] = {
        "provider": provider,
        "request_identity": identity,
        "canonical_uri": (
            "https://arxiv.org/abs/2601.22401"
            if provider == "arXiv"
            else "https://doi.org/10.1234/example"
        ),
        "license_status": license_status,
        "license_basis": "provider record explicitly identifies the license",
        "content_summary": summary,
        "summary_basis": "provider abstract",
        "media_type": "application/pdf" if provider == "arXiv" else "application/json",
        "content_base64": base64.b64encode(content).decode("ascii"),
    }
    if version is not None:
        value["version"] = version
    return value


def response(value: dict[str, object], status: int = 200) -> TransportResponse:
    return TransportResponse(status, json.dumps(value, sort_keys=True).encode("utf-8"))


def adapter(base: LiteratureBase | None, transport: FakeTransport, **kwargs: object) -> LiteratureAdapter:
    return LiteratureAdapter(
        base,
        transport,
        clock=lambda: FIXED_TIME,
        **kwargs,
    )


class LiteratureAdapterTests(unittest.TestCase):
    def test_success_has_bounded_immutable_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            transport = FakeTransport(response(record()))
            result = adapter(LiteratureBase(directory), transport).fetch(Provider.ARXIV, "2601.22401")

            self.assertIsInstance(result, AdapterReport)
            self.assertEqual(result.import_disposition, ImportDisposition.IMPORTED)
            self.assertEqual(result.observation.pinned_version, "v1")  # type: ignore[union-attr]
            self.assertEqual(result.observation.content_digest_sha256, hashlib.sha256(CONTENT).hexdigest())  # type: ignore[union-attr]
            self.assertEqual(result.result.content_size, len(CONTENT))  # type: ignore[union-attr]
            self.assertEqual(result.attempts[0].outcome, "SUCCESS")
            json.loads(result.to_json())
            with self.assertRaises(FrozenInstanceError):
                result.import_disposition = ImportDisposition.PENDING  # type: ignore[misc]
            with self.assertRaises(FrozenInstanceError):
                result.attempts += ()  # type: ignore[misc]

    def test_429_is_retried_once_with_timeout_and_finite_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            transport = FakeTransport(
                TransportResponse(429, b"rate limited"),
                response(record()),
            )
            result = adapter(LiteratureBase(directory), transport, max_retries=1, timeout=2.5).fetch(
                "arxiv", "2601.22401"
            )

            self.assertEqual(result.import_disposition, ImportDisposition.IMPORTED)
            self.assertEqual([item.outcome for item in result.attempts], ["RETRY", "SUCCESS"])
            self.assertEqual(len(transport.calls), 2)
            self.assertEqual(transport.calls[0][1], 2.5)

    def test_permanent_failure_does_not_mutate_literature_base_or_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            transport = FakeTransport(TransportResponse(404, b"missing"), response(record()))
            result = adapter(base, transport, max_retries=3).fetch(Provider.ARXIV, "2601.22401")

            self.assertIsNone(result.import_disposition)
            self.assertEqual(result.result.outcome, "FAILURE")  # type: ignore[union-attr]
            self.assertEqual(len(transport.calls), 1)
            self.assertEqual(base.observations, ())
            self.assertEqual(base.artifacts.records, ())

    def test_oversize_response_does_not_mutate_literature_base(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            transport = FakeTransport(TransportResponse(200, b"x" * 17))
            result = adapter(base, transport, max_bytes=16).fetch(
                Provider.ARXIV,
                "2601.22401",
                record=record(),
            )

            self.assertIsNone(result.import_disposition)
            self.assertEqual(result.attempts[0].outcome, "OVERSIZE")
            self.assertEqual(result.result.outcome, "FAILURE")  # type: ignore[union-attr]
            self.assertEqual(base.observations, ())
            self.assertEqual(base.artifacts.records, ())

    def test_unknown_license_is_pending_without_an_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            transport = FakeTransport(response(record(license_status="UNKNOWN")))
            result = adapter(base, transport).fetch(Provider.ARXIV, "2601.22401")

            self.assertEqual(result.import_disposition, ImportDisposition.PENDING)
            self.assertEqual(result.observation.license_status, LicenseStatus.UNKNOWN)  # type: ignore[union-attr]
            self.assertEqual(result.observation.status, ObservationStatus.PENDING)  # type: ignore[union-attr]
            self.assertEqual(base.artifacts.records, ())

    def test_open_import_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = LiteratureBase(directory)
            transport = FakeTransport(response(record()), response(record()))
            client = adapter(base, transport)
            first = client.fetch(Provider.ARXIV, "2601.22401")
            second = client.fetch(Provider.ARXIV, "2601.22401")

            self.assertEqual(first.import_disposition, ImportDisposition.IMPORTED)
            self.assertEqual(second.import_disposition, ImportDisposition.IDEMPOTENT)
            self.assertEqual(len(base.observations), 1)
            self.assertEqual(len(base.artifacts.records), 1)

    def test_crossref_uses_a_concrete_record_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            value = record(
                provider="Crossref",
                identity="10.1234/Example",
                version=None,
            )
            value["indexed"] = {"date-time": "2026-08-31T12:30:00Z"}
            transport = FakeTransport(response(value))
            result = adapter(LiteratureBase(directory), transport).fetch(
                Provider.CROSSREF, "10.1234/Example"
            )

            self.assertEqual(result.import_disposition, ImportDisposition.IMPORTED)
            self.assertEqual(result.observation.observation_id, "crossref:10.1234/example")  # type: ignore[union-attr]
            self.assertEqual(  # type: ignore[union-attr]
                result.observation.pinned_version,
                "crossref-record:2026-08-31T12:30:00Z",
            )
            self.assertNotEqual(result.observation.pinned_version.lower(), "latest")  # type: ignore[union-attr]

    def test_malformed_provider_date_is_not_accepted_as_a_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            value = record(provider="Crossref", identity="10.1234/Example", version=None)
            value["indexed"] = {}
            result = adapter(LiteratureBase(directory), FakeTransport(response(value))).fetch(
                Provider.CROSSREF, "10.1234/Example"
            )
            self.assertIsNone(result.import_disposition)
            self.assertIn("concrete Crossref version date", result.result.error)  # type: ignore[union-attr]

    def test_status_language_is_rejected_by_source_observation(self) -> None:
        summaries = (
            "The proof is complete.",
            "This is an open problem.",
            "The problem is solved.",
            "A novel contribution is presented.",
        )
        for summary in summaries:
            with self.subTest(summary=summary):
                with self.assertRaises(ValueError):
                    LiteratureAdapter(clock=lambda: FIXED_TIME).normalize_record(
                        record(summary=summary),
                    )

    def test_network_failure_is_retried_but_nontransient_transport_error_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            retrying = FakeTransport(ConnectionError("offline"), response(record()))
            retried = adapter(LiteratureBase(directory), retrying, max_retries=1).fetch(
                Provider.ARXIV, "2601.22401"
            )
            self.assertEqual(retried.import_disposition, ImportDisposition.IMPORTED)
            self.assertEqual([item.outcome for item in retried.attempts], ["RETRY", "SUCCESS"])

            nontransient = FakeTransport(ValueError("bad transport fixture"), response(record()))
            failed = adapter(LiteratureBase(directory), nontransient, max_retries=3).fetch(
                Provider.ARXIV, "2601.22401"
            )
            self.assertIsNone(failed.import_disposition)
            self.assertEqual(len(nontransient.calls), 1)


if __name__ == "__main__":
    unittest.main()
