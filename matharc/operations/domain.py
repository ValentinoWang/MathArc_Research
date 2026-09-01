"""Standalone local operations domain; it intentionally imports no research code."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping, TypeVar
from urllib.parse import parse_qsl, urlsplit


class OperationsDomainError(ValueError): pass


_WORKSPACE_PROVENANCE_KEYS = frozenset(
    {"run_id", "state_digest_sha256", "event_head_hash"}
)
_WORKSPACE_PROVENANCE_OPTIONAL_KEYS = frozenset({"workspace_root"})


_SENSITIVE_METADATA_TOKENS = (
    "secret", "token", "password", "credential", "api_key", "apikey", "authorization",
)
_PUBLIC_METADATA_KEYS = frozenset({"documentation_url", "provider_kind", "region"})
_Record = TypeVar("_Record")

def _canonical(value: object) -> str: return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def _digest(value: object) -> str: return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()
def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip(): raise OperationsDomainError(f"{label} must be non-empty text")
    return value
def _strict(value: object, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected: raise OperationsDomainError(f"{label} has an invalid schema")
    return value


def _workspace_provenance(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or not _WORKSPACE_PROVENANCE_KEYS.issubset(value) or set(value) - (_WORKSPACE_PROVENANCE_KEYS | _WORKSPACE_PROVENANCE_OPTIONAL_KEYS):
        raise OperationsDomainError("workspace provenance has an invalid schema")
    if any(not isinstance(item, str) or not item.strip() for item in value.values()):
        raise OperationsDomainError("workspace provenance must contain non-empty text")
    return {key: value[key] for key in sorted(value)}
def _metadata(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) or not isinstance(item, str) for key, item in value.items()): raise OperationsDomainError("upstream metadata must be a text object")
    if set(value) - _PUBLIC_METADATA_KEYS:
        raise OperationsDomainError("upstream metadata field is not approved for console projection")
    for key, item in value.items():
        if any(token in key.lower() for token in _SENSITIVE_METADATA_TOKENS):
            raise OperationsDomainError("upstream credentials must not be persisted")
        _safe_metadata_value(item)
    return dict(sorted(value.items()))


def _safe_metadata_value(value: str) -> None:
    """Reject credential-bearing URLs even when their field name appears harmless."""
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.netloc:
        return
    if parsed.username is not None or parsed.password is not None:
        raise OperationsDomainError("upstream credentials must not be persisted")
    if any(
        any(token in key.lower() for token in _SENSITIVE_METADATA_TOKENS)
        for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
    ):
        raise OperationsDomainError("upstream credentials must not be persisted")


def _external_root(root: str | Path) -> Path:
    """Keep the independently owned operations store outside research state."""
    resolved = Path(root).resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "workspace.json").is_file():
            raise OperationsDomainError("operations state must be outside a research workspace")
    return resolved

@dataclass(frozen=True, slots=True)
class Account:
    account_id: str
    label: str
    def __post_init__(self) -> None: _text(self.account_id, "account_id"); _text(self.label, "account label")
    def to_dict(self) -> dict[str, str]: return {"account_id": self.account_id, "label": self.label}
    @classmethod
    def from_dict(cls, value: object) -> "Account":
        data = _strict(value, {"account_id", "label"}, "account"); return cls(_text(data["account_id"], "account_id"), _text(data["label"], "account label"))

class CreditDirection(str, Enum): GRANT = "GRANT"; DEBIT = "DEBIT"
@dataclass(frozen=True, slots=True)
class CreditEntry:
    entry_id: str; account_id: str; direction: CreditDirection; amount: int; reason: str
    def __post_init__(self) -> None:
        _text(self.entry_id, "credit entry id"); _text(self.account_id, "credit account id"); _text(self.reason, "credit reason")
        if not isinstance(self.direction, CreditDirection) or not isinstance(self.amount, int) or isinstance(self.amount, bool) or self.amount < 1: raise OperationsDomainError("credit entry is invalid")
    def to_dict(self) -> dict[str, Any]: return {"entry_id": self.entry_id, "account_id": self.account_id, "direction": self.direction.value, "amount": self.amount, "reason": self.reason}
    @classmethod
    def from_dict(cls, value: object) -> "CreditEntry":
        data = _strict(value, {"entry_id", "account_id", "direction", "amount", "reason"}, "credit entry"); return cls(_text(data["entry_id"], "entry_id"), _text(data["account_id"], "account_id"), CreditDirection(data["direction"]), data["amount"], _text(data["reason"], "reason"))

@dataclass(frozen=True, slots=True)
class SeatAllocation:
    allocation_id: str; account_id: str; seats: int
    def __post_init__(self) -> None:
        _text(self.allocation_id, "allocation_id"); _text(self.account_id, "allocation account id")
        if not isinstance(self.seats, int) or isinstance(self.seats, bool) or self.seats < 0: raise OperationsDomainError("seat allocation must be non-negative")
    def to_dict(self) -> dict[str, Any]: return {"allocation_id": self.allocation_id, "account_id": self.account_id, "seats": self.seats}
    @classmethod
    def from_dict(cls, value: object) -> "SeatAllocation":
        data = _strict(value, {"allocation_id", "account_id", "seats"}, "seat allocation"); return cls(_text(data["allocation_id"], "allocation_id"), _text(data["account_id"], "account_id"), data["seats"])

class UpstreamStatus(str, Enum): NOT_CONFIGURED = "not_configured"
@dataclass(frozen=True, slots=True)
class UpstreamConfiguration:
    configuration_id: str; provider_label: str; metadata: Mapping[str, str]; status: UpstreamStatus = UpstreamStatus.NOT_CONFIGURED
    def __post_init__(self) -> None:
        _text(self.configuration_id, "configuration_id"); _text(self.provider_label, "provider_label")
        if self.status is not UpstreamStatus.NOT_CONFIGURED: raise OperationsDomainError("upstream must remain not_configured")
        _metadata(self.metadata)
    def to_dict(self) -> dict[str, Any]: return {"configuration_id": self.configuration_id, "provider_label": self.provider_label, "metadata": _metadata(self.metadata), "status": self.status.value}
    @classmethod
    def from_dict(cls, value: object) -> "UpstreamConfiguration":
        data = _strict(value, {"configuration_id", "provider_label", "metadata", "status"}, "upstream configuration"); return cls(_text(data["configuration_id"], "configuration_id"), _text(data["provider_label"], "provider_label"), _metadata(data["metadata"]), UpstreamStatus(data["status"]))

class OperationsDomainStore:
    """Lock-safe local records with API-append-only credit history.

    State digests detect accidental or partial-file changes.  They are not an
    external tamper-evidence root for an actor that can rewrite the whole file.
    """
    _FILENAME = "operations-domain.json"
    def __init__(self, root: str | Path, *, workspace_provenance: Mapping[str, str] | None = None) -> None:
        self.root = _external_root(root)
        self.path = self.root / self._FILENAME
        self.workspace_provenance = (
            _workspace_provenance(workspace_provenance)
            if workspace_provenance is not None
            else None
        )
    @contextmanager
    def _lock(self) -> Iterator[None]:
        self.root.mkdir(parents=True, exist_ok=True); descriptor = os.open(self.root / ".operations-domain.lock", os.O_CREAT | os.O_RDWR, 0o600)
        try: fcntl.flock(descriptor, fcntl.LOCK_EX); yield
        finally: fcntl.flock(descriptor, fcntl.LOCK_UN); os.close(descriptor)
    def _load(self) -> tuple[list[Account], list[CreditEntry], list[SeatAllocation], list[UpstreamConfiguration]]:
        if not self.path.exists(): return [], [], [], []
        try: raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise OperationsDomainError("operations domain is unreadable") from exc
        base_keys = {
            "schema_version", "accounts", "credits", "seats", "upstreams",
            "state_digest_sha256",
        }
        if self.workspace_provenance is not None and isinstance(raw, Mapping) and set(raw) == base_keys:
            raise OperationsDomainError("workspace-bound operations domain requires provenance")
        expected_keys = set(base_keys)
        if self.workspace_provenance is not None:
            expected_keys.add("workspace_provenance")
        data = _strict(raw, expected_keys, "operations domain")
        persisted_provenance = data.get("workspace_provenance")
        if self.workspace_provenance is None and persisted_provenance is not None:
            raise OperationsDomainError("workspace-bound operations domain requires provenance")
        if self.workspace_provenance is not None and _workspace_provenance(persisted_provenance) != self.workspace_provenance:
            raise OperationsDomainError("operations domain belongs to another workspace")
        unsigned = dict(data); declared = unsigned.pop("state_digest_sha256")
        if data["schema_version"] != "1.0" or declared != _digest(unsigned) or not all(isinstance(data[key], list) for key in ("accounts", "credits", "seats", "upstreams")): raise OperationsDomainError("operations domain integrity check failed")
        accounts = [Account.from_dict(item) for item in data["accounts"]]; credits = [CreditEntry.from_dict(item) for item in data["credits"]]; seats = [SeatAllocation.from_dict(item) for item in data["seats"]]; upstreams = [UpstreamConfiguration.from_dict(item) for item in data["upstreams"]]
        if [item.account_id for item in accounts] != sorted(item.account_id for item in accounts) or len({item.account_id for item in accounts}) != len(accounts) or len({item.entry_id for item in credits}) != len(credits) or [item.allocation_id for item in seats] != sorted(item.allocation_id for item in seats) or len({item.allocation_id for item in seats}) != len(seats) or [item.configuration_id for item in upstreams] != sorted(item.configuration_id for item in upstreams) or len({item.configuration_id for item in upstreams}) != len(upstreams): raise OperationsDomainError("operations domain identities are invalid")
        account_ids = {item.account_id for item in accounts}
        if any(item.account_id not in account_ids for item in credits + seats): raise OperationsDomainError("operations domain contains unknown account reference")
        self._balances(credits); return accounts, credits, seats, upstreams
    @staticmethod
    def _balances(credits: list[CreditEntry]) -> dict[str, int]:
        balances: dict[str, int] = {}
        for item in credits:
            balance = balances.get(item.account_id, 0) + (item.amount if item.direction is CreditDirection.GRANT else -item.amount)
            if balance < 0: raise OperationsDomainError("credit history has a negative balance")
            balances[item.account_id] = balance
        return balances
    def _save(self, accounts: list[Account], credits: list[CreditEntry], seats: list[SeatAllocation], upstreams: list[UpstreamConfiguration]) -> None:
        # Credit ordering is the append-only debit/grant history.  Sorting for
        # display would change its semantics and can fabricate an underflow.
        payload: dict[str, Any] = {"schema_version": "1.0", "accounts": [item.to_dict() for item in sorted(accounts, key=lambda item: item.account_id)], "credits": [item.to_dict() for item in credits], "seats": [item.to_dict() for item in sorted(seats, key=lambda item: item.allocation_id)], "upstreams": [item.to_dict() for item in sorted(upstreams, key=lambda item: item.configuration_id)]}
        if self.workspace_provenance is not None:
            payload["workspace_provenance"] = dict(self.workspace_provenance)
        payload["state_digest_sha256"] = _digest(payload); temporary = self.path.with_suffix(".tmp"); temporary.write_text(_canonical(payload) + "\n", encoding="utf-8"); os.replace(temporary, self.path)
    @staticmethod
    def _add(items: list[_Record], item: _Record, attr: str) -> _Record:
        prior = next((value for value in items if getattr(value, attr) == getattr(item, attr)), None)
        if prior is not None:
            if prior == item: return prior
            raise OperationsDomainError(f"duplicate {attr}")
        items.append(item); return item
    def create_account(self, account: Account) -> Account:
        with self._lock():
            accounts, credits, seats, upstreams = self._load(); result = self._add(accounts, account, "account_id"); self._save(accounts, credits, seats, upstreams); return result
    def record_credit(self, entry: CreditEntry) -> CreditEntry:
        with self._lock():
            accounts, credits, seats, upstreams = self._load()
            if entry.account_id not in {item.account_id for item in accounts}: raise OperationsDomainError("credit references unknown account")
            result = self._add(credits, entry, "entry_id"); self._balances(credits); self._save(accounts, credits, seats, upstreams); return result
    def allocate_seat(self, allocation: SeatAllocation) -> SeatAllocation:
        with self._lock():
            accounts, credits, seats, upstreams = self._load()
            if allocation.account_id not in {item.account_id for item in accounts}: raise OperationsDomainError("seat allocation references unknown account")
            result = self._add(seats, allocation, "allocation_id"); self._save(accounts, credits, seats, upstreams); return result
    def configure_upstream(self, configuration: UpstreamConfiguration) -> UpstreamConfiguration:
        with self._lock():
            accounts, credits, seats, upstreams = self._load(); result = self._add(upstreams, configuration, "configuration_id"); self._save(accounts, credits, seats, upstreams); return result
    def snapshot(self) -> dict[str, Any]:
        accounts, credits, seats, upstreams = self._load(); balances = self._balances(credits)
        persisted = {
            "schema_version": "1.0",
            "accounts": [item.to_dict() for item in accounts],
            "credits": [item.to_dict() for item in credits],
            "seats": [item.to_dict() for item in seats],
            "upstreams": [item.to_dict() for item in upstreams],
        }
        if self.workspace_provenance is not None:
            persisted["workspace_provenance"] = dict(self.workspace_provenance)
        result = {"schema_version": "1.0", "accounts": persisted["accounts"], "credit_balances": dict(sorted(balances.items())), "seat_allocations": persisted["seats"], "upstreams": persisted["upstreams"], "external_identity": "not_configured", "external_payment": "not_configured", "external_upstream": "not_configured", "state_digest_sha256": _digest(persisted)}
        if self.workspace_provenance is not None:
            result["provenance"] = {
                key: value
                for key, value in self.workspace_provenance.items()
                if key in _WORKSPACE_PROVENANCE_KEYS
            }
        return result
