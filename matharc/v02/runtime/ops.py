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

    def healthz(self) -> dict[str, object]:
        return {
            "ok": True,
            "status": "healthy",
            "runtime_run_id": self.runtime_run_id,
            "release_id": self.release_id,
            "store_path": str(self.store_path),
            "event_head_hash": self.store.head_hash,
        }

    def readyz(self) -> dict[str, object]:
        reasons: list[str] = []
        if not self.run_path.is_file():
            reasons.append("run file is missing")
        try:
            validation = self.store.validate()
            if not validation.get("valid"):
                reasons.append("runtime store validation failed")
        except (OSError, RuntimeStoreError) as exc:
            reasons.append(f"runtime store unavailable: {exc}")
        if not self.credential_path.is_file():
            reasons.append("credential is missing")
        return {
            "ok": not reasons,
            "status": "ready" if not reasons else "not_ready",
            "runtime_run_id": self.runtime_run_id,
            "release_id": self.release_id,
            "reasons": reasons,
        }


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
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_runtime_store(store_path: str | Path, destination: str | Path) -> Path:
    """Atomically copy the durable store and bind every copied file by hash."""
    source = Path(store_path).resolve()
    target = Path(destination).resolve()
    if not source.is_dir():
        raise RuntimeBootstrapError(f"runtime store does not exist: {source}")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise RuntimeBootstrapError("runtime store contains a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        staging = Path(temporary) / target.name
        shutil.copytree(source, staging, symlinks=False)
        files = sorted(path for path in staging.rglob("*") if path.is_file())
        manifest = {str(path.relative_to(staging)): _sha256(path) for path in files}
        (staging / "backup-manifest.json").write_text(
            json.dumps({"schema_version": 1, "files": manifest}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if target.exists():
            raise RuntimeBootstrapError(f"backup destination already exists: {target}")
        os.replace(staging, target)
    return target


def cleanup_regenerable(
    runtime_root: str | Path,
    candidates: Iterable[str | Path],
    *,
    backup_path: str | Path,
    protected: Iterable[str | Path] = (),
    allowlist: Iterable[str | Path] | None = None,
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
    backup = backup_runtime_store(root, backup_path)
    for path in resolved:
        path.unlink()
    return {"backup_path": str(backup), "removed": [str(path.relative_to(root)) for path in resolved]}


def _serve(args: argparse.Namespace) -> int:
    runtime = bootstrap_from_env()
    if not runtime.readyz()["ok"]:
        raise RuntimeBootstrapError(json.dumps(runtime.readyz(), sort_keys=True))
    from ...api import serve

    serve(args.run, args.host, args.port, workspace=args.workspace)
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
    args = parser.parse_args(argv)
    if args.command == "serve":
        return _serve(args)
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
