from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterable
from pathlib import Path

REPOSITORY_AUTHORITY_PATHS = ("registry.yaml",)


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _git_output(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_root), *args], text=True
    ).strip()


def _archive_project(repo_root: Path, project_rel: str) -> bytes:
    """Archive the project tree, including the repository-root case."""
    target = "HEAD" if project_rel == "." else f"HEAD:{project_rel}"
    return subprocess.check_output(
        ["git", "-C", str(repo_root), "archive", "--format=tar", target]
    )


def _select_matharc_workflow_paths(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            path
            for path in paths
            if Path(path).parent.as_posix() == ".github/workflows"
            and Path(path).name.startswith("matharc-")
            and Path(path).suffix in {".yml", ".yaml"}
        )
    )


def _archive_paths(
    project_rel: str,
    matharc_workflow_paths: tuple[str, ...],
) -> tuple[str, ...]:
    return (project_rel, *REPOSITORY_AUTHORITY_PATHS, *matharc_workflow_paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prove Gate 0 CI from a clean git-archive project snapshot."
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="archive HEAD even if a Gate 0 input is dirty (not valid for G0-c evidence)",
    )
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parents[1]
    repo_root = Path(_git_output(project_root, "rev-parse", "--show-toplevel"))
    project_rel = project_root.relative_to(repo_root).as_posix()
    workflow_paths = _select_matharc_workflow_paths(
        _git_output(
            repo_root,
            "ls-tree",
            "-r",
            "--name-only",
            "HEAD",
            ".github/workflows",
        ).splitlines()
    )
    if not workflow_paths:
        print("CLEAN-CI REFUSED: HEAD contains no MathArc workflow authority.")
        return 2
    archive_paths = _archive_paths(project_rel, workflow_paths)
    dirty = _git_output(repo_root, "status", "--porcelain", "--", *archive_paths)
    if dirty and not args.allow_dirty:
        print(
            "CLEAN-CI REFUSED: a Gate 0 archive input is dirty. Commit/stash changes before "
            "producing G0-c evidence."
        )
        print(dirty)
        return 2

    head = _git_output(repo_root, "rev-parse", "HEAD")
    project_archive = _archive_project(repo_root, project_rel)
    authority_payloads = {
        path: subprocess.check_output(
            ["git", "-C", str(repo_root), "show", f"HEAD:{path}"]
        )
        for path in archive_paths[1:]
    }

    with tempfile.TemporaryDirectory(prefix="matharc-clean-ci-") as directory:
        clean_repo_root = Path(directory) / "Harness_Engineering"
        clean_root = clean_repo_root / project_rel
        clean_root.mkdir(parents=True)
        with tarfile.open(fileobj=io.BytesIO(project_archive), mode="r:") as handle:
            handle.extractall(clean_root)
        for authority_path, payload in authority_payloads.items():
            target = clean_repo_root / authority_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)

        venv_dir = clean_root / ".venv"
        _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=clean_root)
        if os.name == "nt":
            python = venv_dir / "Scripts" / "python.exe"
            bindir = venv_dir / "Scripts"
        else:
            python = venv_dir / "bin" / "python"
            bindir = venv_dir / "bin"

        # The Xcode Python bundled on macOS may ship pip versions predating
        # PEP 660 editable installs. A regular local install exercises the
        # same packaged source while keeping the clean-checkout gate portable.
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--use-deprecated=legacy-resolver",
                ".[research,dev,formal]",
            ],
            cwd=clean_root,
        )
        env = dict(os.environ)
        env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
        env["PYTHONPATH"] = str(clean_root)
        _run(
            ["make", "ci-full", f"PYTHON={python}"],
            cwd=clean_root,
            env=env,
        )

    print("=== CLEAN CHECKOUT GATE: PASS ===")
    print(f"commit: {head}")
    print("source: committed project tree + registry/workflow authorities")
    print("bootstrap: fresh venv + .[research,dev,formal]")
    print("gate: make ci-full")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
