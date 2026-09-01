"""Bounded, provider-specific retrieval of literature observations.

This module deliberately stops at source observations.  It does not classify
claims, infer source status, or create trace links.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .literature_base import ImportDisposition, LiteratureBase
from .source_observation import LicenseStatus, SourceObservation


class Provider(str, Enum):
    ARXIV = "arXiv"
    CROSSREF = "Crossref"


class TransportError(OSError):
    """A transport failure that may be retried within the finite retry budget."""


class Transport(Protocol):
    def __call__(self, url: str, timeout: float) -> Any:
        ...


@dataclass(frozen=True, slots=True)
class TransportResponse:
    """Small response boundary accepted from an injected transport."""

    status_code: int
    body: bytes
    headers: Mapping[str, str] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status_code, int):
            raise TypeError("status_code must be an int")
        if not isinstance(self.body, bytes):
            raise TypeError("body must be bytes")
        if isinstance(self.headers, Mapping):
            normalized = {str(key): str(value) for key, value in self.headers.items()}
        else:
            normalized = dict(self.headers)
        object.__setattr__(self, "headers", MappingProxyType(normalized))


@dataclass(frozen=True, slots=True)
class AttemptReport:
    """JSON-safe result for one bounded provider request attempt."""

    attempt: int
    request_identity: str
    provider: str
    request_uri: str
    outcome: str
    status_code: int | None = None
    bytes_received: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "request_identity": self.request_identity,
            "provider": self.provider,
            "request_uri": self.request_uri,
            "outcome": self.outcome,
            "status_code": self.status_code,
            "bytes_received": self.bytes_received,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class ResultReport:
    """JSON-safe normalized/import result with no claim semantics."""

    outcome: str
    request_identity: str
    canonical_uri: str | None = None
    pinned_version: str | None = None
    content_digest_sha256: str | None = None
    content_size: int = 0
    media_type: str | None = None
    observation: SourceObservation | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "request_identity": self.request_identity,
            "canonical_uri": self.canonical_uri,
            "pinned_version": self.pinned_version,
            "content_digest_sha256": self.content_digest_sha256,
            "content_size": self.content_size,
            "media_type": self.media_type,
            "observation": self.observation.to_dict() if self.observation is not None else None,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class AdapterReport:
    """Immutable, JSON-safe report for one provider retrieval/import."""

    provider: str
    request_identity: str
    attempts: tuple[AttemptReport, ...]
    results: tuple[ResultReport, ...]
    import_disposition: ImportDisposition | None = None

    @property
    def observation(self) -> SourceObservation | None:
        return self.results[-1].observation if self.results else None

    @property
    def result(self) -> ResultReport | None:
        return self.results[-1] if self.results else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "request_identity": self.request_identity,
            "attempts": tuple(item.to_dict() for item in self.attempts),
            "results": tuple(item.to_dict() for item in self.results),
            "import_disposition": self.import_disposition.value if self.import_disposition is not None else None,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)


LiteratureAdapterReport = AdapterReport
ProviderAdapterReport = AdapterReport
ProviderName = Provider


_ARXIV_API = "https://export.arxiv.org/api/query?id_list={}"
_CROSSREF_API = "https://api.crossref.org/works/{}"
_ARXIV_VERSION = re.compile(r"(?P<version>v[0-9]+)$", re.IGNORECASE)
_STATUS_VALUES = {item.value: item for item in LicenseStatus}
_SUPPORTED_MEDIA_TYPES = {
    "application/json",
    "application/pdf",
    "application/octet-stream",
    "text/html",
    "text/plain",
}


def _provider(value: Provider | str) -> Provider:
    if isinstance(value, Provider):
        return value
    normalized = str(value).strip().lower().replace("-", "")
    if normalized == "arxiv":
        return Provider.ARXIV
    if normalized == "crossref":
        return Provider.CROSSREF
    raise ValueError("provider is not in the frozen allowlist: arXiv, Crossref")


def _unprefixed_identity(provider: Provider, value: str) -> str:
    identity = value.strip()
    if not identity:
        raise ValueError("provider request identity must be non-empty")
    parsed = urlparse(identity)
    if parsed.scheme in {"http", "https"}:
        identity = unquote(parsed.path.rstrip("/").rsplit("/", 1)[-1])
    prefix = provider.value.lower() + ":"
    if identity.lower().startswith(prefix):
        identity = identity[len(prefix) :].strip()
    if provider is Provider.CROSSREF and identity.lower().startswith("doi:"):
        identity = identity[4:].strip()
    if not identity:
        raise ValueError("provider request identity must contain an identifier")
    return identity


def _request_identity(provider: Provider, value: str) -> str:
    identity = _unprefixed_identity(provider, value)
    if provider is Provider.CROSSREF:
        identity = identity.lower()
    return f"{provider.value.lower()}:{identity}"


def _request_uri(provider: Provider, identity: str) -> str:
    value = _unprefixed_identity(provider, identity)
    if provider is Provider.ARXIV:
        return _ARXIV_API.format(quote(value, safe="./"))
    return _CROSSREF_API.format(quote(value, safe=""))


def _utc_timestamp(value: Any = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else str(value).strip()


def _first_value(record: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return None


def _date_value(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key in ("date-time", "date_time", "timestamp", "date"):
            nested = value.get(key)
            if nested:
                return _text(nested)
        parts = value.get("date-parts") or value.get("date_parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            return "-".join(str(item) for item in parts[0])
    if value is not None and not isinstance(value, (Mapping, list, tuple)):
        return _text(value)
    return None


def _concrete_version(provider: Provider, record: Mapping[str, Any], request_value: str) -> str:
    candidate = _first_value(record, "pinned_version", "version", "provider_version")
    if candidate is None and provider is Provider.ARXIV:
        match = _ARXIV_VERSION.search(request_value)
        if match:
            candidate = match.group("version").lower()
        else:
            candidate = _first_value(record, "updated", "published", "published_at")
            if candidate is not None:
                date_value = _date_value(candidate)
                if not date_value:
                    raise ValueError("provider record has no concrete arXiv version date")
                candidate = f"arxiv-updated:{date_value}"
    if candidate is None and provider is Provider.CROSSREF:
        candidate = _first_value(record, "revision", "indexed", "created", "published", "issued")
        if candidate is not None:
            date_value = _date_value(candidate)
            if not date_value:
                raise ValueError("provider record has no concrete Crossref version date")
            candidate = f"crossref-record:{date_value}"
    if candidate is None:
        raise ValueError("provider record has no concrete version")
    version = _text(candidate)
    if not version or version.lower() == "latest":
        raise ValueError("provider record version must be concrete, not latest")
    return version


def _canonical_uri(provider: Provider, record: Mapping[str, Any], request_value: str) -> str:
    candidate = _first_value(record, "canonical_uri", "canonical_url", "uri", "url")
    if candidate is not None:
        return _text(candidate)
    identity = _unprefixed_identity(provider, request_value)
    if provider is Provider.ARXIV:
        return f"https://arxiv.org/abs/{quote(identity, safe='./')}"
    return f"https://doi.org/{quote(identity, safe='/')}"


def _license_status(record: Mapping[str, Any]) -> LicenseStatus:
    value = _first_value(record, "license_status", "licenseStatus")
    if value is None:
        license_value = record.get("license")
        if isinstance(license_value, str) and license_value.strip().upper() in _STATUS_VALUES:
            value = license_value
        elif isinstance(license_value, Mapping):
            value = _first_value(license_value, "status", "license_status")
    if isinstance(value, LicenseStatus):
        return value
    if value is None:
        return LicenseStatus.UNKNOWN
    try:
        return LicenseStatus(_text(value).upper())
    except ValueError as exc:
        raise ValueError("license_status must be OPEN, RESTRICTED, or UNKNOWN") from exc


def _license_basis(record: Mapping[str, Any], status: LicenseStatus) -> str:
    basis = _first_value(record, "license_basis", "licenseBasis")
    if basis is not None:
        return _text(basis)
    if status is LicenseStatus.UNKNOWN:
        return "provider record did not provide an explicit license status"
    return "provider record explicit license status"


def _summary(record: Mapping[str, Any]) -> tuple[str, str]:
    value = _first_value(record, "content_summary", "summary", "abstract", "description")
    if value is None:
        title = record.get("title")
        if isinstance(title, list) and title:
            value = title[0]
        elif title is not None:
            value = title
    if value is None:
        raise ValueError("provider record must include a descriptive summary")
    basis = _first_value(record, "summary_basis", "summaryBasis")
    return _text(value), _text(basis) if basis is not None else "provider record summary"


def _media_type(provider: Provider, record: Mapping[str, Any]) -> str:
    value = _first_value(record, "media_type", "mediaType", "content_type", "mime_type")
    if value is None:
        value = "application/pdf" if provider is Provider.ARXIV else "application/json"
    media_type = _text(value).split(";", 1)[0].strip().lower()
    if media_type not in _SUPPORTED_MEDIA_TYPES:
        raise ValueError(f"unsupported media_type: {media_type}")
    return media_type


def _content_bytes(record: Mapping[str, Any]) -> bytes | None:
    encoded = _first_value(record, "content_base64", "contentBase64")
    if encoded is not None:
        try:
            return base64.b64decode(_text(encoded), validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("content_base64 is invalid") from exc
    value = _first_value(record, "content_bytes", "contentBytes", "content")
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return value.tobytes()
    if isinstance(value, str):
        return value.encode("utf-8")
    raise TypeError("record content must be bytes or a UTF-8 string")


def _digest(record: Mapping[str, Any], content: bytes | None) -> str:
    actual = hashlib.sha256(content).hexdigest() if content is not None else None
    declared = _first_value(record, "content_digest_sha256", "content_sha256", "sha256")
    if declared is not None:
        declared_text = _text(declared)
        if actual is not None and actual != declared_text:
            raise ValueError("content digest does not match normalized bytes")
        return declared_text
    if actual is None:
        raise ValueError("provider record must include content bytes or a content digest")
    return actual


def _record_mapping(record: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    raise TypeError("provider record must be a mapping")


def normalize_provider_record(
    record: Mapping[str, Any],
    *,
    provider: Provider | str | None = None,
    request_identity: str | None = None,
    content: bytes | None = None,
    observed_at: Any = None,
) -> SourceObservation:
    """Normalize one concrete provider record through ``SourceObservation``."""

    values = _record_mapping(record)
    selected_provider = _provider(provider or values.get("provider"))
    raw_identity = request_identity or _first_value(
        values,
        "request_identity",
        "provider_request_identity",
        "identifier",
        "id",
        "doi",
        "DOI",
        "arxiv_id",
    )
    if raw_identity is None:
        raise ValueError("provider record must include a request identity")
    identity = _request_identity(selected_provider, _text(raw_identity))
    provider_value = _unprefixed_identity(selected_provider, _text(raw_identity))
    body = content if content is not None else _content_bytes(values)
    digest = _digest(values, body)
    summary, summary_basis = _summary(values)
    status = _license_status(values)
    return SourceObservation(
        observation_id=identity,
        canonical_uri=_canonical_uri(selected_provider, values, provider_value),
        pinned_version=_concrete_version(selected_provider, values, provider_value),
        observed_at=_utc_timestamp(observed_at if observed_at is not None else values.get("observed_at")),
        license_status=status,
        license_basis=_license_basis(values, status),
        content_summary=summary,
        summary_basis=summary_basis,
        media_type=_media_type(selected_provider, values),
        content_digest_sha256=digest,
    )


normalize_record = normalize_provider_record


def _json_body(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TypeError("transport mapping body must be JSON-serializable") from exc


def _transport_response(raw: Any) -> TransportResponse:
    if isinstance(raw, TransportResponse):
        return raw
    if isinstance(raw, (bytes, bytearray, memoryview)):
        return TransportResponse(200, bytes(raw))
    if isinstance(raw, tuple):
        if len(raw) == 2:
            status, body = raw
            headers: Mapping[str, str] = {}
        elif len(raw) == 3:
            status, headers, body = raw
        else:
            raise TypeError("transport tuple must be (status, body) or (status, headers, body)")
        if isinstance(body, Mapping):
            body = _json_body(body)
        elif not isinstance(body, bytes):
            body = bytes(body)
        return TransportResponse(int(status), body, headers)
    if isinstance(raw, Mapping):
        has_response_shape = any(key in raw for key in ("status_code", "http_status")) or (
            "status" in raw and any(key in raw for key in ("body", "content", "headers"))
        )
        if has_response_shape:
            status = raw.get("status_code", raw.get("http_status", raw.get("status")))
            body = raw.get("body", raw.get("content", b""))
            headers = raw.get("headers", {})
            if isinstance(body, Mapping):
                body = _json_body(body)
            elif not isinstance(body, bytes):
                body = bytes(body)
            return TransportResponse(int(status), body, headers)
        return TransportResponse(200, _json_body(raw))
    status = getattr(raw, "status_code", getattr(raw, "status", None))
    if status is not None:
        body = getattr(raw, "body", getattr(raw, "content", b""))
        if isinstance(body, Mapping):
            body = _json_body(body)
        elif not isinstance(body, bytes):
            body = bytes(body)
        return TransportResponse(int(status), body, getattr(raw, "headers", {}))
    raise TypeError("transport must return TransportResponse, bytes, a response tuple, or a response mapping")


def _arxiv_xml_record(body: bytes) -> dict[str, Any] | None:
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError:
        return None
    atom = "{http://www.w3.org/2005/Atom}"
    entry = root.find(f"{atom}entry")
    if entry is None:
        return None
    values: dict[str, Any] = {}
    for field in ("id", "updated", "published", "title", "summary"):
        node = entry.find(f"{atom}{field}")
        if node is not None and node.text:
            values[field] = " ".join(node.text.split())
    for link in entry.findall(f"{atom}link"):
        if link.attrib.get("title") == "pdf" and link.attrib.get("href"):
            values["canonical_uri"] = link.attrib["href"]
            break
    identifier = values.get("id")
    if isinstance(identifier, str):
        values["request_identity"] = identifier.rsplit("/", 1)[-1]
        values.pop("id", None)
    return values


def _provider_payload(provider: Provider, body: bytes) -> tuple[dict[str, Any], bytes]:
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        decoded = _arxiv_xml_record(body) if provider is Provider.ARXIV else None
    if isinstance(decoded, Mapping):
        payload = dict(decoded)
        message = payload.get("message")
        if provider is Provider.CROSSREF and isinstance(message, Mapping):
            payload = dict(message)
        return payload, body
    return {}, body


def _default_transport(url: str, timeout: float, max_bytes: int) -> TransportResponse:
    request = Request(url, headers={"Accept": "application/json, application/atom+xml, application/xml;q=0.9"})
    try:
        with urlopen(request, timeout=timeout) as response:
            status = int(response.getcode() or 200)
            body = response.read(max_bytes + 1)
            headers = dict(response.headers.items())
            return TransportResponse(status, body, headers)
    except HTTPError as exc:
        return TransportResponse(int(exc.code), exc.read(max_bytes + 1), dict(exc.headers.items()))


class LiteratureAdapter:
    """Retrieve allowlisted provider records with bounded, injected IO."""

    def __init__(
        self,
        literature_base: LiteratureBase | None = None,
        transport: Transport | Callable[[str, float], Any] | None = None,
        *,
        base: LiteratureBase | None = None,
        timeout: float = 10.0,
        max_bytes: int = 5 * 1024 * 1024,
        max_retries: int = 2,
        clock: Callable[[], Any] | None = None,
    ) -> None:
        if literature_base is not None and base is not None:
            raise TypeError("pass either literature_base or base, not both")
        if literature_base is None:
            literature_base = base
        if not isinstance(timeout, (int, float)) or not math.isfinite(float(timeout)) or timeout <= 0:
            raise ValueError("timeout must be a finite positive number")
        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
            raise ValueError("max_bytes must be a positive integer")
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        self.literature_base = literature_base
        self.transport = transport
        self.timeout = float(timeout)
        self.max_bytes = max_bytes
        self.max_retries = max_retries
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def normalize_record(
        self,
        record: Mapping[str, Any],
        *,
        provider: Provider | str | None = None,
        request_identity: str | None = None,
        content: bytes | None = None,
        observed_at: Any = None,
    ) -> SourceObservation:
        return normalize_provider_record(
            record,
            provider=provider,
            request_identity=request_identity,
            content=content,
            observed_at=observed_at if observed_at is not None else self.clock(),
        )

    def fetch(
        self,
        provider: Provider | str,
        request_identity: str,
        *,
        record: Mapping[str, Any] | None = None,
        content: bytes | None = None,
        observed_at: Any = None,
        source_filename: str = "",
    ) -> AdapterReport:
        selected_provider = _provider(provider)
        identity = _request_identity(selected_provider, request_identity)
        request_uri = _request_uri(selected_provider, identity)
        attempts: list[AttemptReport] = []
        for attempt_number in range(1, self.max_retries + 2):
            try:
                response = self._transport(request_uri)
            except (TransportError, TimeoutError, OSError) as exc:
                retry = attempt_number <= self.max_retries
                attempts.append(
                    AttemptReport(
                        attempt=attempt_number,
                        request_identity=identity,
                        provider=selected_provider.value,
                        request_uri=request_uri,
                        outcome="RETRY" if retry else "FAILURE",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                if retry:
                    continue
                return self._failure_report(selected_provider, identity, attempts, "transport failure")
            except Exception as exc:
                attempts.append(
                    AttemptReport(
                        attempt=attempt_number,
                        request_identity=identity,
                        provider=selected_provider.value,
                        request_uri=request_uri,
                        outcome="FAILURE",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                return self._failure_report(selected_provider, identity, attempts, "transport failure")

            body_size = len(response.body)
            transient = response.status_code == 429 or 500 <= response.status_code <= 599
            if not 200 <= response.status_code < 300:
                retry = transient and attempt_number <= self.max_retries
                attempts.append(
                    AttemptReport(
                        attempt=attempt_number,
                        request_identity=identity,
                        provider=selected_provider.value,
                        request_uri=request_uri,
                        outcome="RETRY" if retry else "FAILURE",
                        status_code=response.status_code,
                        bytes_received=body_size,
                        error=f"provider returned HTTP {response.status_code}",
                    )
                )
                if retry:
                    continue
                return self._failure_report(selected_provider, identity, attempts, "provider request failed")
            if body_size > self.max_bytes:
                attempts.append(
                    AttemptReport(
                        attempt=attempt_number,
                        request_identity=identity,
                        provider=selected_provider.value,
                        request_uri=request_uri,
                        outcome="OVERSIZE",
                        status_code=response.status_code,
                        bytes_received=body_size,
                        error=f"response exceeds max_bytes={self.max_bytes}",
                    )
                )
                return self._failure_report(selected_provider, identity, attempts, "response exceeds max_bytes")

            attempts.append(
                AttemptReport(
                    attempt=attempt_number,
                    request_identity=identity,
                    provider=selected_provider.value,
                    request_uri=request_uri,
                    outcome="SUCCESS",
                    status_code=response.status_code,
                    bytes_received=body_size,
                )
            )
            payload, raw_body = _provider_payload(selected_provider, response.body)
            if record is not None:
                supplied = _record_mapping(record)
                supplied.update(payload)
                payload = supplied
            if content is not None:
                payload["content_bytes"] = content
            elif _content_bytes(payload) is None:
                payload["content_bytes"] = raw_body
            payload.setdefault("provider", selected_provider.value)
            payload.setdefault("request_identity", identity)
            try:
                observation = self.normalize_record(
                    payload,
                    provider=selected_provider,
                    request_identity=identity,
                    observed_at=observed_at,
                )
            except (TypeError, ValueError) as exc:
                return self._failure_report(selected_provider, identity, attempts, str(exc))
            imported_content = _content_bytes(payload)
            if imported_content is None:
                return self._failure_report(selected_provider, identity, attempts, "normalized record has no content")
            if len(imported_content) > self.max_bytes:
                attempts[-1] = AttemptReport(
                    attempt=attempts[-1].attempt,
                    request_identity=attempts[-1].request_identity,
                    provider=attempts[-1].provider,
                    request_uri=attempts[-1].request_uri,
                    outcome="OVERSIZE",
                    status_code=attempts[-1].status_code,
                    bytes_received=len(imported_content),
                    error=f"content exceeds max_bytes={self.max_bytes}",
                )
                return self._failure_report(selected_provider, identity, attempts, "content exceeds max_bytes")
            return self._import_report(
                selected_provider,
                identity,
                attempts,
                observation,
                imported_content,
                source_filename or _text(_first_value(payload, "source_filename", "filename") or ""),
            )
        raise AssertionError("finite retry loop exhausted without a report")

    retrieve = fetch

    def import_record(
        self,
        provider: Provider | str,
        request_identity: str,
        record: Mapping[str, Any],
        content: bytes,
        *,
        observed_at: Any = None,
        source_filename: str = "",
    ) -> AdapterReport:
        selected_provider = _provider(provider)
        identity = _request_identity(selected_provider, request_identity)
        try:
            observation = self.normalize_record(
                record,
                provider=selected_provider,
                request_identity=identity,
                content=content,
                observed_at=observed_at,
            )
        except (TypeError, ValueError) as exc:
            result = ResultReport("FAILURE", identity, error=str(exc))
            return AdapterReport(selected_provider.value, identity, (), (result,), None)
        if len(content) > self.max_bytes:
            result = ResultReport(
                "OVERSIZE",
                identity,
                canonical_uri=observation.canonical_uri,
                pinned_version=observation.pinned_version,
                content_digest_sha256=observation.content_digest_sha256,
                content_size=len(content),
                media_type=observation.media_type,
                error=f"content exceeds max_bytes={self.max_bytes}",
            )
            return AdapterReport(selected_provider.value, identity, (), (result,), None)
        return self._import_report(selected_provider, identity, [], observation, content, source_filename)

    def _transport(self, request_uri: str) -> TransportResponse:
        if self.transport is None:
            return _default_transport(request_uri, self.timeout, self.max_bytes)
        raw = self.transport(request_uri, self.timeout)
        return _transport_response(raw)

    def _failure_report(
        self,
        provider: Provider,
        identity: str,
        attempts: list[AttemptReport],
        error: str,
    ) -> AdapterReport:
        result = ResultReport("FAILURE", identity, error=error)
        return AdapterReport(provider.value, identity, tuple(attempts), (result,), None)

    def _import_report(
        self,
        provider: Provider,
        identity: str,
        attempts: list[AttemptReport],
        observation: SourceObservation,
        content: bytes,
        source_filename: str,
    ) -> AdapterReport:
        disposition: ImportDisposition | None = None
        result_observation = observation
        error: str | None = None
        outcome = "NORMALIZED"
        if self.literature_base is not None:
            imported = self.literature_base.import_bytes(
                observation,
                content,
                source_filename=source_filename,
            )
            disposition = imported.disposition
            result_observation = imported.observation
            outcome = disposition.value
            error = imported.reason or None
        result = ResultReport(
            outcome,
            identity,
            canonical_uri=result_observation.canonical_uri,
            pinned_version=result_observation.pinned_version,
            content_digest_sha256=result_observation.content_digest_sha256,
            content_size=len(content),
            media_type=result_observation.media_type,
            observation=result_observation,
            error=error,
        )
        return AdapterReport(provider.value, identity, tuple(attempts), (result,), disposition)


ProviderAdapter = LiteratureAdapter


__all__ = [
    "AdapterReport",
    "AttemptReport",
    "ImportDisposition",
    "LiteratureAdapter",
    "LiteratureAdapterReport",
    "LicenseStatus",
    "Provider",
    "ProviderAdapter",
    "ProviderAdapterReport",
    "ProviderName",
    "ResultReport",
    "SourceObservation",
    "Transport",
    "TransportError",
    "TransportResponse",
    "normalize_provider_record",
    "normalize_record",
]
