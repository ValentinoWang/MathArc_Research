"""Persistent, reviewable storage for imported literature observations."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .artifact_store import ArtifactRecord, ArtifactStore
from .budget import BudgetLedger
from .source_observation import LicenseStatus, ObservationStatus, SourceObservation


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
        self.budget = budget
        self._observations: dict[str, SourceObservation] = {}
        if self.manifest_path.is_file():
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or set(payload) != {"schema_version", "observations"}:
                raise ValueError("invalid literature observation manifest")
            if payload["schema_version"] != "1.0":
                raise ValueError("unsupported literature observation schema")
            for item in payload["observations"]:
                observation = SourceObservation.from_dict(item)
                if observation.observation_id in self._observations:
                    raise ValueError("duplicate observation id")
                self._observations[observation.observation_id] = observation
            self._validate_observed_artifacts()

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
                            artifact = self._verified_artifact(item.artifact_id, item.content_digest_sha256)
                        except (KeyError, ValueError) as exc:
                            rejected = self._rejected(observation)
                            return ImportResult(ImportDisposition.REJECTED, rejected, reason=f"artifact integrity failure: {exc}")
                        return ImportResult(ImportDisposition.IDEMPOTENT, item, artifact, "same identity and digest")
                    if (
                        item.content_digest_sha256
                        and observation.content_digest_sha256
                        and item.content_digest_sha256 != observation.content_digest_sha256
                    ):
                        conflict_id = observation.observation_id
                        if conflict_id in self._observations:
                            conflict_id = f"{conflict_id}-conflict-{observation.content_digest_sha256[:8]}"
                        conflict = SourceObservation.from_dict(
                            {**observation.to_dict(), "observation_id": conflict_id, "status": ObservationStatus.CONFLICT.value, "artifact_id": None}
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
                    conflict_id = observation.observation_id
                    if conflict_id in self._observations:
                        conflict_id = f"{conflict_id}-conflict-{observation.content_digest_sha256[:8]}"
                    conflict = SourceObservation.from_dict(
                        {**observation.to_dict(), "observation_id": conflict_id, "status": ObservationStatus.CONFLICT.value, "artifact_id": None}
                    )
                    self._record(conflict)
                    return ImportResult(ImportDisposition.CONFLICT, conflict, reason="same identity has a different digest")

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

    def _record(self, observation: SourceObservation) -> None:
        self._observations[observation.observation_id] = observation
        payload = {
            "schema_version": "1.0",
            "observations": [item.to_dict() for item in self.observations],
        }
        temporary = self.manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.manifest_path)

    def _verified_artifact(self, artifact_id: str, expected_digest: str) -> ArtifactRecord:
        artifact = self.artifacts.get(artifact_id)
        path = self.artifacts.path_for(artifact_id)
        if artifact.sha256 != expected_digest or not path.is_file():
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
                self._verified_artifact(observation.artifact_id, observation.content_digest_sha256)
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
            self._verified_artifact(artifact_id, actual_digest)
            return existing
        return self.artifacts.put_bytes(
            artifact_id,
            content,
            logical_role="literature-observation",
            producer="matharc-literature-base",
            media_type=observation.media_type,
            source_filename=source_filename,
        )
