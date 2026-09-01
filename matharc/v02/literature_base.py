"""Persistent, reviewable storage for imported literature observations."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .artifact_store import ArtifactRecord, ArtifactStore
from .budget import BudgetLedger
from .source_observation import LicenseStatus, ObservationStatus, SourceObservation

TOPIC_OBSERVATION_TRANSACTION_PATH_NAME = ".topic-observation-transaction.json"
TOPIC_OBSERVATION_RETIRED_TRANSACTION_PATH_NAME = (
    ".topic-observation-transaction.retiring.json"
)
_WRITER_LOCK_STATE = threading.local()


def _thread_lock_paths(name: str) -> set[str]:
    paths = getattr(_WRITER_LOCK_STATE, name, None)
    if paths is None:
        paths = set()
        setattr(_WRITER_LOCK_STATE, name, paths)
    return paths


def _literature_root_key(root: Path) -> str:
    return str(_canonical_literature_root(root))


def _canonical_literature_root(root: Path) -> Path:
    try:
        canonical_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("literature root is unreadable") from exc
    if not canonical_root.is_dir():
        raise ValueError("literature root is not a directory")
    return canonical_root


def _topic_transaction_pending(root: Path) -> bool:
    canonical_root = _canonical_literature_root(root)
    for path_name in (
        TOPIC_OBSERVATION_TRANSACTION_PATH_NAME,
        TOPIC_OBSERVATION_RETIRED_TRANSACTION_PATH_NAME,
    ):
        try:
            (canonical_root.parent / path_name).lstat()
        except FileNotFoundError:
            continue
        except OSError:
            return True
        return True
    return False


@contextmanager
def literature_writer_lock(
    root: str | Path,
    *,
    allow_topic_transaction: bool = False,
) -> Iterator[None]:
    """Serialize all writers, including a topic transaction spanning many imports."""

    literature_root = Path(root)
    literature_root.mkdir(parents=True, exist_ok=True)
    root_key = _literature_root_key(literature_root)
    held_paths = _thread_lock_paths("held_paths")
    authorized_paths = _thread_lock_paths("authorized_paths")
    if root_key in held_paths:
        added_authority = allow_topic_transaction and root_key not in authorized_paths
        if added_authority:
            authorized_paths.add(root_key)
        try:
            yield
        finally:
            if added_authority:
                authorized_paths.remove(root_key)
        return

    lock_path = literature_root / ".observations.lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise ValueError("literature writer lock is unreadable") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("literature writer lock is not a regular file")
        lock_file = os.fdopen(descriptor, "a+", encoding="utf-8")
        descriptor = -1
    except Exception:
        if descriptor != -1:
            os.close(descriptor)
        raise
    with lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        held_paths.add(root_key)
        if allow_topic_transaction:
            authorized_paths.add(root_key)
        try:
            yield
        finally:
            authorized_paths.discard(root_key)
            held_paths.remove(root_key)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _topic_transaction_authorized(root: Path) -> bool:
    return _literature_root_key(root) in _thread_lock_paths("authorized_paths")


class ImportDisposition(str, Enum):
    IMPORTED = "IMPORTED"
    IDEMPOTENT = "IDEMPOTENT"
    PENDING = "PENDING"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class ImportResult:
    disposition: ImportDisposition
    observation: SourceObservation
    artifact: ArtifactRecord | None = None
    reason: str = ""


class LiteratureBase:
    """Keep literature observations separate from verified mathematical claims."""

    def __init__(self, root: str | Path, budget: BudgetLedger | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.artifacts = ArtifactStore.load(self.root / "artifacts")
        self.manifest_path = self.root / "observations.json"
        self.lock_path = self.root / ".observations.lock"
        self.budget = budget
        self._observations: dict[str, SourceObservation] = {}
        self._reload_state()

    @property
    def observations(self) -> tuple[SourceObservation, ...]:
        return tuple(self._observations[key] for key in sorted(self._observations))

    def import_file(self, observation: SourceObservation, source: str | Path) -> ImportResult:
        path = Path(source)
        return self.import_bytes(observation, path.read_bytes(), source_filename=path.name)

    def import_bytes(
        self,
        observation: SourceObservation,
        content: bytes,
        *,
        source_filename: str = "",
    ) -> ImportResult:
        with self._writer_lock():
            if _topic_transaction_pending(self.root) and not _topic_transaction_authorized(
                self.root
            ):
                return ImportResult(
                    ImportDisposition.REJECTED,
                    self._rejected(observation),
                    reason="topic observation transaction recovery is pending",
                )
            try:
                self._reload_state()
            except (KeyError, ValueError) as exc:
                return ImportResult(
                    ImportDisposition.REJECTED,
                    self._rejected(observation),
                    reason=f"stored state integrity failure: {exc}",
                )
            return self._import_bytes_locked(
                observation,
                content,
                source_filename=source_filename,
            )

    def _import_bytes_locked(
        self,
        observation: SourceObservation,
        content: bytes,
        *,
        source_filename: str,
    ) -> ImportResult:
        actual_digest = hashlib.sha256(content).hexdigest()
        existing_id = self._observations.get(observation.observation_id)
        if existing_id is not None and existing_id.logical_identity != observation.logical_identity:
            rejected = self._rejected(observation)
            return ImportResult(ImportDisposition.REJECTED, rejected, reason="observation_id already names another logical identity")
        existing_identity = sorted(
            (item for item in self.observations if item.logical_identity == observation.logical_identity),
            key=lambda item: item.status is not ObservationStatus.OBSERVED,
        )
        if existing_identity:
            for item in existing_identity:
                if item.status is ObservationStatus.OBSERVED:
                    if (
                        item.content_digest_sha256 == observation.content_digest_sha256
                        and item.content_digest_sha256
                        and item.artifact_id is not None
                    ):
                        if observation.license_status is not LicenseStatus.OPEN:
                            return ImportResult(
                                ImportDisposition.REJECTED,
                                item,
                                reason="observed replay requires confirmed open license",
                            )
                        if self.budget is not None and self.budget.exhausted():
                            return ImportResult(
                                ImportDisposition.REJECTED,
                                item,
                                reason="observed replay blocked by exhausted budget",
                            )
                        if actual_digest != observation.content_digest_sha256:
                            return ImportResult(
                                ImportDisposition.REJECTED,
                                item,
                                reason="imported bytes do not match the declared digest",
                            )
                        try:
                            artifact = self._verified_artifact(
                                item.artifact_id,
                                item.content_digest_sha256,
                                expected_media_type=item.media_type,
                            )
                        except (KeyError, ValueError) as exc:
                            rejected = self._rejected(observation)
                            return ImportResult(ImportDisposition.REJECTED, rejected, reason=f"artifact integrity failure: {exc}")
                        return ImportResult(ImportDisposition.IDEMPOTENT, item, artifact, "same identity and digest")
                    if (
                        item.content_digest_sha256
                        and observation.content_digest_sha256
                        and item.content_digest_sha256 != observation.content_digest_sha256
                    ):
                        conflict = self._conflict(observation)
                        if conflict is None:
                            rejected = self._rejected(observation)
                            return ImportResult(
                                ImportDisposition.REJECTED,
                                rejected,
                                reason="derived conflict observation_id already names another record",
                            )
                        self._record(conflict)
                        return ImportResult(ImportDisposition.CONFLICT, conflict, reason="same identity has a different digest")
                    return ImportResult(
                        ImportDisposition.REJECTED,
                        item,
                        reason="observed record cannot be downgraded or replaced by an incomplete retry",
                    )
                if (
                    item.content_digest_sha256
                    and observation.content_digest_sha256
                    and item.content_digest_sha256 == observation.content_digest_sha256
                ):
                    # A pending record is intentionally revalidated below so a
                    # later license/digest confirmation can complete import.
                    continue
                if (
                    item.content_digest_sha256
                    and observation.content_digest_sha256
                    and item.content_digest_sha256 != observation.content_digest_sha256
                ):
                    conflict = self._conflict(observation)
                    if conflict is None:
                        rejected = self._rejected(observation)
                        return ImportResult(
                            ImportDisposition.REJECTED,
                            rejected,
                            reason="derived conflict observation_id already names another record",
                        )
                    self._record(conflict)
                    return ImportResult(ImportDisposition.CONFLICT, conflict, reason="same identity has a different digest")

        for existing in self._observations.values():
            if (
                existing.observation_id != observation.observation_id
                and existing.idempotency_key == observation.idempotency_key
            ):
                rejected = self._rejected(observation)
                return ImportResult(
                    ImportDisposition.REJECTED,
                    rejected,
                    reason="observation idempotency key already names another record",
                )

        if self.budget is not None and self.budget.exhausted():
            pending = self._pending(observation)
            self._record(pending)
            return ImportResult(ImportDisposition.PENDING, pending, reason="budget exhausted")
        if observation.license_status is not LicenseStatus.OPEN:
            pending = self._pending(observation)
            self._record(pending)
            return ImportResult(ImportDisposition.PENDING, pending, reason="license is not confirmed open")
        if not observation.content_digest_sha256:
            pending = self._pending(observation)
            self._record(pending)
            return ImportResult(ImportDisposition.PENDING, pending, reason="content digest is missing")
        if actual_digest != observation.content_digest_sha256:
            pending = self._pending(observation)
            self._record(pending)
            return ImportResult(ImportDisposition.PENDING, pending, reason="content digest mismatch")

        artifact_id = "lit-" + hashlib.sha256(
            f"{observation.logical_identity}|{actual_digest}".encode("utf-8")
        ).hexdigest()[:32]
        try:
            artifact = self._reuse_or_put_artifact(
                artifact_id,
                content,
                observation,
                source_filename,
            )
        except (KeyError, ValueError) as exc:
            pending = self._pending(observation)
            self._record(pending)
            return ImportResult(ImportDisposition.PENDING, pending, reason=f"artifact persistence failed: {exc}")
        observed = SourceObservation.from_dict(
            {**observation.to_dict(), "status": ObservationStatus.OBSERVED.value, "artifact_id": artifact.artifact_id}
        )
        self._record(observed)
        return ImportResult(ImportDisposition.IMPORTED, observed, artifact)

    def _pending(self, observation: SourceObservation) -> SourceObservation:
        return SourceObservation.from_dict(
            {**observation.to_dict(), "status": ObservationStatus.PENDING.value, "artifact_id": None}
        )

    def _rejected(self, observation: SourceObservation) -> SourceObservation:
        return SourceObservation.from_dict(
            {**observation.to_dict(), "status": ObservationStatus.REJECTED.value, "artifact_id": None}
        )

    def _conflict(self, observation: SourceObservation) -> SourceObservation | None:
        """Build a deterministic conflict ID without replacing any stored record."""

        identity_digest = hashlib.sha256(
            f"{observation.logical_identity}|{observation.content_digest_sha256}".encode("utf-8")
        ).hexdigest()
        conflict_id = f"{observation.observation_id}-conflict-{identity_digest}"
        conflict = SourceObservation.from_dict(
            {
                **observation.to_dict(),
                "observation_id": conflict_id,
                "status": ObservationStatus.CONFLICT.value,
                "artifact_id": None,
            }
        )
        existing = self._observations.get(conflict_id)
        if existing is not None and existing.to_dict() != conflict.to_dict():
            return None
        return conflict

    @contextmanager
    def _writer_lock(self) -> Iterator[None]:
        with literature_writer_lock(self.root):
            yield

    def _reload_state(self) -> None:
        self.artifacts = ArtifactStore.load(self.root / "artifacts")
        self._observations = {}
        if not self.manifest_path.is_file():
            return
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or set(payload) != {"schema_version", "observations"}:
            raise ValueError("invalid literature observation manifest")
        if payload["schema_version"] != "1.0":
            raise ValueError("unsupported literature observation schema")
        if not isinstance(payload["observations"], list):
            raise ValueError("invalid literature observation manifest")
        observation_keys: dict[str, str] = {}
        for item in payload["observations"]:
            observation = SourceObservation.from_dict(item)
            if observation.observation_id in self._observations:
                raise ValueError("duplicate observation id")
            existing_observation_id = observation_keys.get(observation.idempotency_key)
            if (
                existing_observation_id is not None
                and existing_observation_id != observation.observation_id
            ):
                raise ValueError("duplicate observation idempotency key")
            observation_keys[observation.idempotency_key] = observation.observation_id
            self._observations[observation.observation_id] = observation
        self._validate_observed_artifacts()

    def _record(self, observation: SourceObservation) -> None:
        existing = self._observations.get(observation.observation_id)
        if existing is not None and existing.to_dict() != observation.to_dict():
            if (
                existing.logical_identity != observation.logical_identity
                or existing.status is not ObservationStatus.PENDING
            ):
                raise ValueError(f"refusing to overwrite observation id: {observation.observation_id}")
        for existing in self._observations.values():
            if (
                existing.observation_id != observation.observation_id
                and existing.idempotency_key == observation.idempotency_key
            ):
                raise ValueError("refusing to record duplicate observation idempotency key")
        self._observations[observation.observation_id] = observation
        payload = {
            "schema_version": "1.0",
            "observations": [item.to_dict() for item in self.observations],
        }
        temporary = self.manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.manifest_path)

    def _verified_artifact(
        self,
        artifact_id: str,
        expected_digest: str,
        *,
        expected_media_type: str | None = None,
    ) -> ArtifactRecord:
        artifact = self.artifacts.get(artifact_id)
        path = self.artifacts.path_for(artifact_id)
        if (
            artifact.sha256 != expected_digest
            or not path.is_file()
            or artifact.logical_role != "literature-observation"
            or artifact.producer != "matharc-literature-base"
            or (expected_media_type is not None and artifact.media_type != expected_media_type)
        ):
            raise ValueError("artifact reference is not intact")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != artifact.sha256:
            raise ValueError("artifact blob digest mismatch")
        if len(content) != artifact.size_bytes:
            raise ValueError("artifact blob size mismatch")
        return artifact

    def _validate_observed_artifacts(self) -> None:
        for observation in self._observations.values():
            if observation.status is not ObservationStatus.OBSERVED:
                continue
            if not observation.artifact_id or not observation.content_digest_sha256:
                raise ValueError(f"observed record has incomplete artifact reference: {observation.observation_id}")
            try:
                self._verified_artifact(
                    observation.artifact_id,
                    observation.content_digest_sha256,
                    expected_media_type=observation.media_type,
                )
            except (KeyError, ValueError) as exc:
                raise ValueError(f"invalid artifact for observed record {observation.observation_id}: {exc}") from exc

    def _reuse_or_put_artifact(
        self,
        artifact_id: str,
        content: bytes,
        observation: SourceObservation,
        source_filename: str,
    ) -> ArtifactRecord:
        try:
            existing = self.artifacts.get(artifact_id)
        except KeyError:
            existing = None
        actual_digest = hashlib.sha256(content).hexdigest()
        if existing is not None:
            if (
                existing.sha256 != actual_digest
                or existing.size_bytes != len(content)
                or existing.logical_role != "literature-observation"
                or existing.producer != "matharc-literature-base"
                or existing.media_type != observation.media_type
            ):
                raise ValueError("existing artifact metadata conflicts with imported content")
            self._verified_artifact(
                artifact_id,
                actual_digest,
                expected_media_type=observation.media_type,
            )
            return existing
        return self.artifacts.put_bytes(
            artifact_id,
            content,
            logical_role="literature-observation",
            producer="matharc-literature-base",
            media_type=observation.media_type,
            source_filename=source_filename,
        )
