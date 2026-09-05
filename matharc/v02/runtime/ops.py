"""Deployment bootstrap and conservative runtime operations.

This module is intentionally independent of the HTTP server.  The systemd
entrypoint calls ``serve`` so deployment inputs are validated before the API
opens a socket, while the operation helpers remain usable by an operator or
test without requiring a running server.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ..trace import RuntimeQuota, StructuredRuntimeLogger
from .run_store import RuntimeStore, RuntimeStoreError


class RuntimeBootstrapError(RuntimeError):
    """Raised when deployment inputs cannot establish a safe runtime."""


@dataclass(frozen=True, slots=True)
class RuntimeBootstrap:
    runtime_run_id: str
    release_id: str
    run_path: Path
    workspace: Path
    store_path: Path
    backup_path: Path
    log_path: Path
    credential_path: Path
    store: RuntimeStore
    logger: StructuredRuntimeLogger | None = None
    quota: RuntimeQuota | None = None
    policy: dict[str, object] | None = None

    def healthz(self) -> dict[str, object]:
        payload = {
            "ok": True,
            "status": "healthy",
            "runtime_run_id": self.runtime_run_id,
            "release_id": self.release_id,
            "store_path": str(self.store_path),
            "event_head_hash": self.store.head_hash,
        }
        if self.quota is not None:
            payload["quota"] = self.quota.snapshot()
        if self.policy is not None:
            payload["policy"] = dict(self.policy)
        return payload

    def readyz(self) -> dict[str, object]:
        reasons: list[str] = []
        run_manifest: dict[str, object] | None = None
        if not self.run_path.is_file():
            reasons.append("run file is missing")
        else:
            try:
                run_manifest = _read_run_manifest(
                    self.run_path,
                    runtime_run_id=self.runtime_run_id,
                    release_id=self.release_id,
                )
            except RuntimeBootstrapError as exc:
                reasons.append(str(exc))
        configured_workspace_manifest = os.environ.get("MATHARC_WORKSPACE_MANIFEST", "").strip()
        workspace_manifest = self.workspace / "workspace.json"
        workspace_manifest_payload: dict[str, object] | None = None
        if configured_workspace_manifest:
            configured_path = Path(configured_workspace_manifest)
            if not configured_path.is_absolute() or configured_path.resolve() != workspace_manifest.resolve():
                reasons.append("workspace manifest path is not bound to workspace")
            else:
                workspace_manifest = configured_path
        if not workspace_manifest.is_file():
            reasons.append("workspace manifest is missing")
        else:
            try:
                workspace_manifest_payload = _validate_workspace_manifest(
                    self.workspace,
                    runtime_run_id=self.runtime_run_id,
                )
            except RuntimeBootstrapError as exc:
                reasons.append(str(exc))
        try:
            validation = self.store.validate()
            if not validation.get("valid"):
                reasons.append("runtime store validation failed")
        except (OSError, RuntimeStoreError) as exc:
            reasons.append(f"runtime store unavailable: {exc}")
        if not self.credential_path.is_file():
            reasons.append("credential is missing")
        payload: dict[str, object] = {
            "ok": not reasons,
            "status": "ready" if not reasons else "not_ready",
            "runtime_run_id": self.runtime_run_id,
            "release_id": self.release_id,
            "reasons": reasons,
        }
        if run_manifest is not None:
            payload["run_manifest"] = run_manifest
        if workspace_manifest_payload is not None:
            payload["workspace_manifest"] = workspace_manifest_payload
        return payload


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or "REPLACE-ME" in value:
        raise RuntimeBootstrapError(f"{name} must be a concrete deployment value")
    return value


def _path_env(name: str, *, default: str | None = None) -> Path:
    value = os.environ.get(name, default or "").strip()
    if not value:
        raise RuntimeBootstrapError(f"{name} is required")
    path = Path(value)
    if not path.is_absolute():
        raise RuntimeBootstrapError(f"{name} must be an absolute path")
    return path


def _credential_path() -> Path:
    configured = os.environ.get("MATHARC_SECRET_FILE", "").strip()
    credential_dir = os.environ.get("CREDENTIALS_DIRECTORY", "").strip()
    if configured.startswith("%d/"):
        if not credential_dir:
            raise RuntimeBootstrapError("CREDENTIALS_DIRECTORY is required for %d credential paths")
        return Path(credential_dir) / configured[3:]
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            raise RuntimeBootstrapError("MATHARC_SECRET_FILE must be absolute or %d-relative")
        return path
    if credential_dir:
        return Path(credential_dir) / "api-token"
    raise RuntimeBootstrapError("external api credential is not configured")


def _optional_path_env(name: str) -> Path | None:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        raise RuntimeBootstrapError(f"{name} must be an absolute path")
    return path


def _bool_env(name: str, *, default: bool = False) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeBootstrapError(f"{name} must be a boolean")


def _number_env(name: str, *, default: float) -> float:
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    try:
        number = float(value)
    except ValueError as exc:
        raise RuntimeBootstrapError(f"{name} must be a positive number") from exc
    if number <= 0:
        raise RuntimeBootstrapError(f"{name} must be a positive number")
    return number


def _read_json(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeBootstrapError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeBootstrapError(f"{label} must be a JSON object")
    return value


def _read_run_manifest(path: Path, *, runtime_run_id: str, release_id: str) -> dict[str, object]:
    payload = _read_json(path, "run manifest")
    actual_run_id = str(payload.get("runtime_run_id", payload.get("run_id", "")))
    actual_release_id = str(payload.get("release_id", ""))
    if actual_run_id != runtime_run_id:
        raise RuntimeBootstrapError("run manifest runtime_run_id mismatch")
    if actual_release_id != release_id:
        raise RuntimeBootstrapError("run manifest release_id mismatch")
    digest = payload.get("manifest_digest_sha256")
    if digest is not None:
        unsigned = {key: value for key, value in payload.items() if key != "manifest_digest_sha256"}
        if str(digest) != _digest_json(unsigned):
            raise RuntimeBootstrapError("run manifest digest mismatch")
    return payload


def _digest_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _validate_workspace_manifest(root: Path, *, runtime_run_id: str | None = None) -> dict[str, object]:
    manifest = _read_json(root / "workspace.json", "workspace manifest")
    if str(manifest.get("schema_version")) != "1.0":
        raise RuntimeBootstrapError("unsupported workspace manifest schema")
    run_id = str(manifest.get("run_id", ""))
    if not run_id:
        raise RuntimeBootstrapError("workspace manifest run_id is missing")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise RuntimeBootstrapError("workspace manifest files are missing")
    for relative, expected in files.items():
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise RuntimeBootstrapError("workspace manifest contains an unsafe path")
        path = (root / relative).resolve()
        if root.resolve() not in path.parents or not path.is_file():
            raise RuntimeBootstrapError(f"workspace manifest file is missing: {relative}")
        if _sha256(path) != str(expected):
            raise RuntimeBootstrapError(f"workspace manifest digest mismatch: {relative}")
    # ResearchWorkspace.load performs the cross-file state/event digest checks.
    try:
        from ..workspace import ResearchWorkspace
        workspace = ResearchWorkspace.load(root)
    except Exception as exc:  # convert implementation details to a readiness reason
        raise RuntimeBootstrapError(f"workspace manifest validation failed: {exc}") from exc
    if workspace.trace.run_id != run_id:
        raise RuntimeBootstrapError("workspace manifest run_id mismatch")
    if runtime_run_id and manifest.get("runtime_run_id") not in (None, runtime_run_id):
        raise RuntimeBootstrapError("workspace manifest runtime_run_id mismatch")
    return manifest


def bootstrap_from_env() -> RuntimeBootstrap:
    """Consume deployment env and create/reopen the durable runtime identity."""
    runtime_run_id = _required_env("MATHARC_RUNTIME_RUN_ID")
    release_id = _required_env("MATHARC_RELEASE_ID")
    run_path = _path_env("MATHARC_RUN_PATH")
    workspace = _path_env("MATHARC_WORKSPACE")
    store_path = _path_env("MATHARC_STORE_PATH", default=str(workspace / "runtime-store"))
    backup_path = _path_env("MATHARC_BACKUP_PATH")
    log_path = _path_env("MATHARC_LOG_PATH")
    credential_path = _credential_path()
    try:
        credential = credential_path.read_bytes()
    except OSError as exc:
        raise RuntimeBootstrapError("external api credential is unreadable") from exc
    if not credential_path.is_file() or not credential.strip():
        raise RuntimeBootstrapError("external api credential is missing or empty")
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        store = RuntimeStore(store_path)
        store.create_run(
            {
                "runtime_run_id": runtime_run_id,
                "release_id": release_id,
                "workspace_id": str(workspace),
                "trace_id": runtime_run_id,
                "generation_id": "bootstrap",
            }
        )
    except RuntimeStoreError as exc:
        raise RuntimeBootstrapError(str(exc)) from exc
    try:
        quota = RuntimeQuota(
            per_user=_number_env("MATHARC_PER_USER_QUOTA", default=100),
            global_limit=_number_env("MATHARC_GLOBAL_QUOTA", default=1000),
        )
    except ValueError as exc:
        raise RuntimeBootstrapError(str(exc)) from exc
    policy = {
        "startup_timeout_seconds": _number_env("MATHARC_STARTUP_TIMEOUT_SECONDS", default=30),
        "cancel_policy": os.environ.get("MATHARC_CANCEL_POLICY", "SIGTERM_THEN_TIMEOUT").strip(),
        "failure_policy": os.environ.get("MATHARC_FAILURE_POLICY", "classify_and_restart").strip(),
        "rollback_release_id": os.environ.get("MATHARC_ROLLBACK_RELEASE_ID", "").strip() or None,
    }
    if not policy["cancel_policy"] or not policy["failure_policy"]:
        raise RuntimeBootstrapError("cancel and failure policies must be configured")
    logger = StructuredRuntimeLogger(log_path)
    logger.emit(
        "runtime.bootstrap",
        runtime_run_id=runtime_run_id,
        release_id=release_id,
        policy=policy,
    )
    return RuntimeBootstrap(
        runtime_run_id,
        release_id,
        run_path,
        workspace,
        store_path,
        backup_path,
        log_path,
        credential_path,
        store,
        logger,
        quota,
        policy,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_runtime_store(
    store_path: str | Path,
    destination: str | Path,
    *,
    runtime_run_id: str | None = None,
    release_id: str | None = None,
) -> Path:
    """Atomically copy a durable store and bind every copied file by hash."""
    source = Path(store_path).resolve()
    target = Path(destination).resolve()
    if not source.is_dir():
        raise RuntimeBootstrapError(f"runtime store does not exist: {source}")
    if target == source or source in target.parents:
        raise RuntimeBootstrapError("backup destination must be outside runtime store")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise RuntimeBootstrapError("runtime store contains a symlink")
    if runtime_run_id is None or release_id is None:
        try:
            runs = RuntimeStore(source).state.get("runs", {})
            if len(runs) == 1:
                run = next(iter(runs.values()))
                runtime_run_id = runtime_run_id or str(run.get("runtime_run_id", "")) or None
                release_id = release_id or str(run.get("release_id", "")) or None
        except RuntimeStoreError as exc:
            raise RuntimeBootstrapError(f"runtime store is invalid: {exc}") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        staging = Path(temporary) / target.name
        shutil.copytree(source, staging, symlinks=False)
        files = sorted(path for path in staging.rglob("*") if path.is_file())
        manifest = {str(path.relative_to(staging)): _sha256(path) for path in files}
        manifest_payload = {
            "schema_version": 1,
            "runtime_run_id": runtime_run_id,
            "release_id": release_id,
            "files": manifest,
        }
        manifest_payload["manifest_digest_sha256"] = _digest_json(manifest_payload)
        (staging / "backup-manifest.json").write_text(
            json.dumps(manifest_payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if target.exists():
            raise RuntimeBootstrapError(f"backup destination already exists: {target}")
        os.replace(staging, target)
    return target


def _verify_backup(backup: Path, *, runtime_run_id: str | None = None, release_id: str | None = None) -> dict[str, object]:
    if not backup.is_dir():
        raise RuntimeBootstrapError(f"backup does not exist: {backup}")
    manifest_path = backup / "backup-manifest.json"
    payload = _read_json(manifest_path, "backup manifest")
    if payload.get("schema_version") != 1 or not isinstance(payload.get("files"), dict):
        raise RuntimeBootstrapError("unsupported backup manifest")
    actual_run_id = payload.get("runtime_run_id")
    actual_release_id = payload.get("release_id")
    if runtime_run_id is not None and actual_run_id not in (None, runtime_run_id):
        raise RuntimeBootstrapError("backup runtime_run_id mismatch")
    if release_id is not None and actual_release_id not in (None, release_id):
        raise RuntimeBootstrapError("backup release_id mismatch")
    declared_digest = payload.get("manifest_digest_sha256")
    if declared_digest:
        unsigned = {key: value for key, value in payload.items() if key != "manifest_digest_sha256"}
        if str(declared_digest) != _digest_json(unsigned):
            raise RuntimeBootstrapError("backup manifest digest mismatch")
    for relative, expected in payload["files"].items():
        path = (backup / str(relative)).resolve()
        if backup not in path.parents or not path.is_file():
            raise RuntimeBootstrapError(f"backup file is missing: {relative}")
        if _sha256(path) != str(expected):
            raise RuntimeBootstrapError(f"backup file digest mismatch: {relative}")
    return payload


def restore_runtime_store(
    backup: str | Path,
    destination: str | Path,
    *,
    runtime_run_id: str | None = None,
    release_id: str | None = None,
    expected_digest: str | None = None,
) -> Path:
    """Verify a backup manifest and atomically restore it into a new path."""
    source = Path(backup).resolve()
    target = Path(destination).resolve()
    payload = _verify_backup(source, runtime_run_id=runtime_run_id, release_id=release_id)
    if expected_digest and str(payload.get("manifest_digest_sha256")) != expected_digest:
        raise RuntimeBootstrapError("backup manifest digest does not match expected digest")
    if target.exists():
        raise RuntimeBootstrapError(f"restore destination already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        staging = Path(temporary) / target.name
        shutil.copytree(source, staging, symlinks=False, ignore=shutil.ignore_patterns("backup-manifest.json"))
        os.replace(staging, target)
    return target


def rollback_runtime_store(
    backup: str | Path,
    destination: str | Path,
    *,
    runtime_run_id: str | None = None,
    release_id: str | None = None,
    expected_digest: str | None = None,
) -> Path:
    """Rollback is a named, identity-checked restore operation."""
    target = Path(destination).resolve()
    if not target.exists():
        return restore_runtime_store(
            backup,
            target,
            runtime_run_id=runtime_run_id,
            release_id=release_id,
            expected_digest=expected_digest,
        )
    # Stage and validate the replacement first, then switch the directory
    # entry atomically. The old store is retained until the new one is ready.
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        staged = Path(temporary) / target.name
        restore_runtime_store(
            backup,
            staged,
            runtime_run_id=runtime_run_id,
            release_id=release_id,
            expected_digest=expected_digest,
        )
        old = Path(temporary) / f"{target.name}.previous"
        os.replace(target, old)
        try:
            os.replace(staged, target)
        except Exception:
            os.replace(old, target)
            raise
        shutil.rmtree(old)
    return target


# Explicit aliases keep the operator-facing vocabulary discoverable while
# retaining the precise runtime-store names used by the implementation.
restore_runtime_backup = restore_runtime_store
rollback_runtime = rollback_runtime_store


def cleanup_regenerable(
    runtime_root: str | Path,
    candidates: Iterable[str | Path],
    *,
    backup_path: str | Path,
    protected: Iterable[str | Path] = (),
    allowlist: Iterable[str | Path] | None = None,
    runtime_run_id: str | None = None,
    release_id: str | None = None,
) -> dict[str, object]:
    """Back up first, then remove only explicit files under the runtime root."""
    root = Path(runtime_root).resolve()
    if not root.is_dir():
        raise RuntimeBootstrapError(f"runtime root does not exist: {root}")
    names = [Path(item) for item in candidates]
    allowed = {Path(item) for item in allowlist} if allowlist is not None else set(names)
    protected_paths = {(root / Path(item)).resolve() for item in protected}
    resolved: list[Path] = []
    for item in names:
        if item not in allowed:
            raise RuntimeBootstrapError(f"cleanup candidate is not allowlisted: {item}")
        path = (root / item).resolve()
        if path == root or root not in path.parents:
            raise RuntimeBootstrapError("cleanup candidate escapes runtime root")
        if path in protected_paths:
            raise RuntimeBootstrapError(f"cleanup candidate is protected: {item}")
        if path.is_symlink() or not path.is_file():
            raise RuntimeBootstrapError(f"cleanup candidate must be a regular file: {item}")
        resolved.append(path)
    backup = backup_runtime_store(
        root,
        backup_path,
        runtime_run_id=runtime_run_id,
        release_id=release_id,
    )
    for path in resolved:
        path.unlink()
    return {"backup_path": str(backup), "removed": [str(path.relative_to(root)) for path in resolved]}


cleanup_runtime = cleanup_regenerable


def _serve(args: argparse.Namespace) -> int:
    runtime = bootstrap_from_env()
    if not runtime.readyz()["ok"]:
        raise RuntimeBootstrapError(json.dumps(runtime.readyz(), sort_keys=True))
    # The deployment entrypoint must expose the v0.2 workspace observatory.
    # Keep all optional edge/access configuration in the environment so the
    # systemd unit and local bootstrap use the same server constructor.
    from ..workspace_server import make_server

    dashboard_path = _optional_path_env("MATHARC_DASHBOARD_PATH")
    access_store_path = _optional_path_env("MATHARC_ACCESS_STORE_PATH")
    access_api = None
    admin_api = None
    admin_dashboard_path = _optional_path_env("MATHARC_ADMIN_DASHBOARD_PATH")
    if _bool_env("MATHARC_ADMIN_ENABLED"):
        from ..access import PostgresInvitationAccessStore
        from ..access_server import AccessAPI
        from ..admin_server import AdminAPI
        from ..admin_service import AdminService, psycopg_connection_factory
        dsn = os.environ.get("MATHARC_ADMIN_DATABASE_URL", "").strip()
        if not dsn:
            raise RuntimeBootstrapError("MATHARC_ADMIN_DATABASE_URL is required when MATHARC_ADMIN_ENABLED=true")
        if not _bool_env("MATHARC_ADMIN_TRUST_PROXY"):
            raise RuntimeBootstrapError("MATHARC_ADMIN_TRUST_PROXY must be true when admin API is enabled")
        # Schema creation is an explicit migration step; serving must never
        # create a partial schema that can mask an incomplete deployment.
        admin_service = AdminService(psycopg_connection_factory(dsn))
        admin_api = AdminAPI(admin_service, trusted_proxy=_bool_env("MATHARC_ADMIN_TRUST_PROXY"))
        access_api = AccessAPI(
            PostgresInvitationAccessStore(psycopg_connection_factory(dsn)),
            cookie_secure=_bool_env("MATHARC_ACCESS_COOKIE_SECURE"),
        )
    server = make_server(
        runtime.workspace,
        host=args.host,
        port=args.port,
        dashboard_path=dashboard_path,
        access_store_root=access_store_path,
        access_api=access_api,
        access_cookie_secure=_bool_env("MATHARC_ACCESS_COOKIE_SECURE"),
        admin_api=admin_api,
        admin_dashboard_path=admin_dashboard_path,
        runtime_store_path=runtime.store_path,
    )
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    serve_parser = sub.add_parser("serve")
    serve_parser.add_argument("--run", required=True)
    serve_parser.add_argument("--host", required=True)
    serve_parser.add_argument("--port", type=int, required=True)
    serve_parser.add_argument("--workspace", required=True)
    sub.add_parser("healthz")
    sub.add_parser("readyz")
    backup_parser = sub.add_parser("backup")
    backup_parser.add_argument("--source", required=True)
    backup_parser.add_argument("--destination", required=True)
    backup_parser.add_argument("--runtime-run-id")
    backup_parser.add_argument("--release-id")
    for command in ("restore", "rollback"):
        operation = sub.add_parser(command)
        operation.add_argument("--backup", required=True)
        operation.add_argument("--destination", required=True)
        operation.add_argument("--runtime-run-id")
        operation.add_argument("--release-id")
        operation.add_argument("--expected-digest")
    cleanup_parser = sub.add_parser("cleanup")
    cleanup_parser.add_argument("--root", required=True)
    cleanup_parser.add_argument("--backup", required=True)
    cleanup_parser.add_argument("--candidate", action="append", required=True)
    cleanup_parser.add_argument("--protected", action="append", default=[])
    cleanup_parser.add_argument("--allowlist", action="append")
    cleanup_parser.add_argument("--runtime-run-id")
    cleanup_parser.add_argument("--release-id")
    args = parser.parse_args(argv)
    if args.command == "serve":
        return _serve(args)
    if args.command == "backup":
        result = backup_runtime_store(
            args.source,
            args.destination,
            runtime_run_id=args.runtime_run_id,
            release_id=args.release_id,
        )
        print(json.dumps({"backup_path": str(result)}, sort_keys=True))
        return 0
    if args.command in {"restore", "rollback"}:
        operation = rollback_runtime_store if args.command == "rollback" else restore_runtime_store
        result = operation(
            args.backup,
            args.destination,
            runtime_run_id=args.runtime_run_id,
            release_id=args.release_id,
            expected_digest=args.expected_digest,
        )
        print(json.dumps({"destination": str(result), "operation": args.command}, sort_keys=True))
        return 0
    if args.command == "cleanup":
        result = cleanup_regenerable(
            args.root,
            args.candidate,
            backup_path=args.backup,
            protected=args.protected,
            allowlist=args.allowlist,
            runtime_run_id=args.runtime_run_id,
            release_id=args.release_id,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    runtime = bootstrap_from_env()
    if args.command == "healthz":
        print(json.dumps(runtime.healthz(), sort_keys=True))
        return 0
    if args.command == "readyz":
        payload = runtime.readyz()
        print(json.dumps(payload, sort_keys=True))
        return 0 if payload["ok"] else 1
    raise RuntimeBootstrapError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
