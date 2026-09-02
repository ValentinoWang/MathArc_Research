from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import canonical_json, digest_json, utc_now


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_fd = os.open(directory, flags)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _ensure_directory_durable(path: str | Path) -> None:
    directory = Path(path)
    if not directory.is_absolute():
        directory = Path.cwd() / directory
    missing: list[Path] = []
    current = directory
    while True:
        try:
            current.stat()
        except FileNotFoundError:
            missing.append(current)
        else:
            if not current.is_dir():
                raise NotADirectoryError(f"directory path is not a directory: {current}")
            break
        parent = current.parent
        if parent == current:
            raise FileNotFoundError(f"could not find directory parent: {current}")
        current = parent

    for child in reversed(missing):
        try:
            child.mkdir()
        except FileExistsError:
            if not child.is_dir():
                raise
            continue
        _fsync_directory(child.parent)


def _durable_atomic_replace(path: str | Path, content: bytes) -> Path:
    target = Path(path)
    if not target.is_absolute():
        target = Path.cwd() / target
    _ensure_directory_durable(target.parent)
    temporary_path: Path | None = None
    open_fd = -1
    renamed = False
    try:
        open_fd, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(open_fd, "wb") as temporary_file:
            open_fd = -1
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, target)
        renamed = True
        _fsync_directory(target.parent)
        return target
    finally:
        if open_fd != -1:
            os.close(open_fd)
        if not renamed and temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


@dataclass(slots=True)
class ArtifactRecord:
    artifact_id: str
    sha256: str
    size_bytes: int
    media_type: str
    relative_path: str
    logical_role: str
    producer: str
    linked_claim_ids: tuple[str, ...] = ()
    linked_tool_call_ids: tuple[str, ...] = ()
    source_filename: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "media_type": self.media_type,
            "relative_path": self.relative_path,
            "logical_role": self.logical_role,
            "producer": self.producer,
            "linked_claim_ids": list(self.linked_claim_ids),
            "linked_tool_call_ids": list(self.linked_tool_call_ids),
            "source_filename": self.source_filename,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ArtifactRecord":
        allowed = {
            "artifact_id",
            "sha256",
            "size_bytes",
            "media_type",
            "relative_path",
            "logical_role",
            "producer",
            "linked_claim_ids",
            "linked_tool_call_ids",
            "source_filename",
            "created_at",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown artifact-record fields: {sorted(unknown)}")
        return cls(
            artifact_id=str(payload["artifact_id"]),
            sha256=str(payload["sha256"]),
            size_bytes=int(payload["size_bytes"]),
            media_type=str(payload["media_type"]),
            relative_path=str(payload["relative_path"]),
            logical_role=str(payload["logical_role"]),
            producer=str(payload["producer"]),
            linked_claim_ids=tuple(
                str(item) for item in payload.get("linked_claim_ids", [])
            ),
            linked_tool_call_ids=tuple(
                str(item) for item in payload.get("linked_tool_call_ids", [])
            ),
            source_filename=str(payload.get("source_filename", "")),
            created_at=str(payload.get("created_at") or utc_now()),
        )


class ArtifactStore:
    """Content-addressed storage for certificates, logs, sources and reports."""

    def __init__(
        self,
        root: str | Path,
        records: Iterable[ArtifactRecord] = (),
    ) -> None:
        self.root = Path(root)
        self.blob_root = self.root / "sha256"
        self.manifest_path = self.root / "manifest.json"
        _ensure_directory_durable(self.blob_root)
        self._records: dict[str, ArtifactRecord] = {}
        for record in records:
            self._add_record(record)

    @property
    def records(self) -> tuple[ArtifactRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def get(self, artifact_id: str) -> ArtifactRecord:
        try:
            return self._records[artifact_id]
        except KeyError as exc:
            raise KeyError(f"unknown artifact: {artifact_id}") from exc

    def path_for(self, artifact_id: str) -> Path:
        record = self.get(artifact_id)
        path = (self.root / record.relative_path).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError(f"artifact path escapes store root: {record.relative_path}")
        return path

    def put_bytes(
        self,
        artifact_id: str,
        content: bytes,
        *,
        logical_role: str,
        producer: str,
        media_type: str = "application/octet-stream",
        linked_claim_ids: Iterable[str] = (),
        linked_tool_call_ids: Iterable[str] = (),
        source_filename: str = "",
    ) -> ArtifactRecord:
        if artifact_id in self._records:
            raise ValueError(f"duplicate artifact id: {artifact_id}")
        sha256 = hashlib.sha256(content).hexdigest()
        relative_path = Path("sha256") / sha256[:2] / sha256
        target = self.root / relative_path
        _ensure_directory_durable(target.parent)
        if target.exists():
            with target.open("rb") as existing_file:
                existing = existing_file.read()
                if existing != content:
                    raise ValueError(f"content-address collision at {target}")
                os.fsync(existing_file.fileno())
            _fsync_directory(target.parent)
        else:
            _durable_atomic_replace(target, content)
        record = ArtifactRecord(
            artifact_id=artifact_id,
            sha256=sha256,
            size_bytes=len(content),
            media_type=media_type,
            relative_path=relative_path.as_posix(),
            logical_role=logical_role,
            producer=producer,
            linked_claim_ids=tuple(str(item) for item in linked_claim_ids),
            linked_tool_call_ids=tuple(str(item) for item in linked_tool_call_ids),
            source_filename=source_filename,
        )
        candidate_records = dict(self._records)
        self._add_record_to(candidate_records, record)
        self._save_manifest(candidate_records)
        self._records = candidate_records
        return record

    def put_text(
        self,
        artifact_id: str,
        text: str,
        *,
        logical_role: str,
        producer: str,
        media_type: str = "text/plain; charset=utf-8",
        linked_claim_ids: Iterable[str] = (),
        linked_tool_call_ids: Iterable[str] = (),
        source_filename: str = "",
    ) -> ArtifactRecord:
        return self.put_bytes(
            artifact_id,
            text.encode("utf-8"),
            logical_role=logical_role,
            producer=producer,
            media_type=media_type,
            linked_claim_ids=linked_claim_ids,
            linked_tool_call_ids=linked_tool_call_ids,
            source_filename=source_filename,
        )

    def put_json(
        self,
        artifact_id: str,
        value: Any,
        *,
        logical_role: str,
        producer: str,
        linked_claim_ids: Iterable[str] = (),
        linked_tool_call_ids: Iterable[str] = (),
        source_filename: str = "",
    ) -> ArtifactRecord:
        text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        return self.put_text(
            artifact_id,
            text,
            logical_role=logical_role,
            producer=producer,
            media_type="application/json; charset=utf-8",
            linked_claim_ids=linked_claim_ids,
            linked_tool_call_ids=linked_tool_call_ids,
            source_filename=source_filename,
        )

    def import_file(
        self,
        artifact_id: str,
        source: str | Path,
        *,
        logical_role: str,
        producer: str,
        media_type: str | None = None,
        linked_claim_ids: Iterable[str] = (),
        linked_tool_call_ids: Iterable[str] = (),
    ) -> ArtifactRecord:
        path = Path(source)
        guessed = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return self.put_bytes(
            artifact_id,
            path.read_bytes(),
            logical_role=logical_role,
            producer=producer,
            media_type=media_type or guessed,
            linked_claim_ids=linked_claim_ids,
            linked_tool_call_ids=linked_tool_call_ids,
            source_filename=path.name,
        )

    def verify(self) -> dict[str, Any]:
        errors: list[str] = []
        verified = 0
        for record in self._records.values():
            try:
                path = self.path_for(record.artifact_id)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not path.is_file():
                errors.append(f"artifact file is missing: {record.artifact_id}")
                continue
            content = path.read_bytes()
            actual = hashlib.sha256(content).hexdigest()
            if actual != record.sha256:
                errors.append(f"artifact digest mismatch: {record.artifact_id}")
                continue
            if len(content) != record.size_bytes:
                errors.append(f"artifact size mismatch: {record.artifact_id}")
                continue
            verified += 1
        return {
            "valid": not errors,
            "errors": errors,
            "artifact_count": len(self._records),
            "verified_count": verified,
            "manifest_digest_sha256": digest_json(self.to_dict()),
        }

    def to_dict(self) -> dict[str, Any]:
        return self._manifest_dict(self._records)

    @staticmethod
    def _manifest_dict(records: Mapping[str, ArtifactRecord]) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "content_addressing": "sha256",
            "records": [records[key].to_dict() for key in sorted(records)],
        }

    def save_manifest(self) -> Path:
        self._save_manifest(self._records)
        return self.manifest_path

    def _save_manifest(self, records: Mapping[str, ArtifactRecord]) -> None:
        content = (
            json.dumps(
                self._manifest_dict(records),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        _durable_atomic_replace(self.manifest_path, content)

    @classmethod
    def load(cls, root: str | Path) -> "ArtifactStore":
        root_path = Path(root)
        manifest = root_path / "manifest.json"
        if not manifest.is_file():
            return cls(root_path)
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("artifact manifest root must be an object")
        if set(payload) - {"schema_version", "content_addressing", "records"}:
            raise ValueError("unknown artifact-manifest fields")
        if str(payload.get("schema_version")) != "1.0":
            raise ValueError("unsupported artifact-manifest schema")
        if str(payload.get("content_addressing")) != "sha256":
            raise ValueError("unsupported artifact addressing scheme")
        store = cls(
            root_path,
            (ArtifactRecord.from_dict(item) for item in payload.get("records", [])),
        )
        verification = store.verify()
        if not verification["valid"]:
            raise ValueError("; ".join(verification["errors"]))
        return store

    def _add_record(self, record: ArtifactRecord) -> None:
        self._add_record_to(self._records, record)

    @staticmethod
    def _add_record_to(
        records: dict[str, ArtifactRecord],
        record: ArtifactRecord,
    ) -> None:
        if record.artifact_id in records:
            existing = records[record.artifact_id]
            if existing.to_dict() != record.to_dict():
                raise ValueError(f"conflicting artifact id: {record.artifact_id}")
            return
        if len(record.sha256) != 64:
            raise ValueError(f"artifact {record.artifact_id} has invalid SHA-256")
        records[record.artifact_id] = record
