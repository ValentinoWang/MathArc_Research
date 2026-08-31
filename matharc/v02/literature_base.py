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
        existing_id = self._observations.get(observation.observation_id)
        if existing_id is not None and existing_id.logical_identity != observation.logical_identity:
            rejected = self._rejected(observation)
            return ImportResult(ImportDisposition.REJECTED, rejected, reason="observation_id already names another logical identity")
        existing_identity = [item for item in self.observations if item.logical_identity == observation.logical_identity]
        if existing_identity:
            for item in existing_identity:
                if (
                    item.content_digest_sha256 == observation.content_digest_sha256
                    and item.content_digest_sha256
                    and item.status is ObservationStatus.OBSERVED
                    and item.artifact_id is not None
                ):
                    try:
                        artifact = self.artifacts.get(item.artifact_id)
                        artifact_path = self.artifacts.path_for(item.artifact_id)
                        if artifact.sha256 != item.content_digest_sha256 or not artifact_path.is_file():
                            raise ValueError("artifact reference is not intact")
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
        actual_digest = hashlib.sha256(content).hexdigest()
        if actual_digest != observation.content_digest_sha256:
            pending = self._pending(observation)
            self._record(pending)
            return ImportResult(ImportDisposition.PENDING, pending, reason="content digest mismatch")

        artifact_id = "lit-" + hashlib.sha256(
            f"{observation.logical_identity}|{actual_digest}".encode("utf-8")
        ).hexdigest()[:32]
        artifact = self.artifacts.put_bytes(
            artifact_id,
            content,
            logical_role="literature-observation",
            producer="matharc-literature-base",
            media_type=observation.media_type,
            source_filename=source_filename,
        )
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
