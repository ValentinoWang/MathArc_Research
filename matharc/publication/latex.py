from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True, slots=True)
class BibliographyWorkflow:
    mode: str
    bib_files: tuple[Path, ...]
    bbl_files: tuple[Path, ...]


def detect_bibliography_workflow(source_root: str | Path) -> BibliographyWorkflow:
    root = Path(source_root)
    tex_files = tuple(sorted(root.rglob("*.tex"))) if root.is_dir() else (root,)
    text = "\n".join(path.read_text(encoding="utf-8") for path in tex_files if path.is_file())
    bib_files = tuple(sorted(root.rglob("*.bib"))) if root.is_dir() else tuple(root.parent.glob("*.bib"))
    bbl_files = tuple(sorted(root.rglob("*.bbl"))) if root.is_dir() else tuple(root.parent.glob("*.bbl"))
    uses_bibliography = "\\bibliography" in text or "\\addbibresource" in text or "\\printbibliography" in text
    if not uses_bibliography:
        return BibliographyWorkflow("none", bib_files, bbl_files)
    if bib_files and bbl_files:
        return BibliographyWorkflow("bib-and-bbl", bib_files, bbl_files)
    if bib_files:
        return BibliographyWorkflow("bib", bib_files, bbl_files)
    if bbl_files:
        return BibliographyWorkflow("bbl", bib_files, bbl_files)
    return BibliographyWorkflow("missing", bib_files, bbl_files)


def bibliography_errors(source_root: str | Path) -> list[str]:
    workflow = detect_bibliography_workflow(source_root)
    if workflow.mode == "missing":
        return ["LaTeX references are used but neither .bib nor .bbl is present"]
    if workflow.mode == "bib":
        return ["LaTeX references have .bib but no .bbl; arXiv does not run BibTeX"]
    return []


_INCLUDE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")


def collect_latex_sources(entrypoint: str | Path) -> tuple[Path, ...]:
    """Return an entrypoint and its input/include tree, rejecting cycles/missing files."""
    entry = Path(entrypoint).resolve()
    visited: set[Path] = set()
    active: set[Path] = set()
    ordered: list[Path] = []

    def visit(path: Path) -> None:
        path = path.resolve()
        if path in active:
            raise ValueError(f"LaTeX include cycle detected at {path}")
        if path in visited:
            return
        if not path.is_file():
            raise ValueError(f"included LaTeX source is missing: {path}")
        active.add(path)
        visited.add(path)
        ordered.append(path)
        text = path.read_text(encoding="utf-8")
        for match in _INCLUDE.finditer(text):
            target = path.parent / match.group(1).strip()
            if target.suffix == "":
                target = target.with_suffix(".tex")
            visit(target)
        active.remove(path)

    visit(entry)
    return tuple(ordered)


def available_compilers() -> tuple[str, ...]:
    return tuple(name for name in ("latexmk", "pdflatex", "bibtex", "biber") if shutil.which(name))


def compile_latex(source: str | Path, *, timeout_seconds: int = 120) -> tuple[bool, str]:
    """Compile a source tree with an explicit fallback and readable failure."""
    main = Path(source)
    root = main.parent
    if not main.is_file():
        return False, f"missing LaTeX entrypoint: {main}"
    workflow = detect_bibliography_workflow(root)
    if workflow.mode in {"missing", "bib"}:
        return False, "references are declared but no .bib/.bbl is available"
    if shutil.which("latexmk"):
        command = ["latexmk", "-pdf", "-interaction=nonstopmode", main.name]
    elif shutil.which("pdflatex"):
        command = ["pdflatex", "-interaction=nonstopmode", main.name]
    else:
        return False, "no supported LaTeX compiler (latexmk or pdflatex) is installed"
    try:
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                   timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired:
        return False, f"LaTeX compilation timed out after {timeout_seconds}s"
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip().splitlines()[-1:]
        return False, "LaTeX compilation failed" + (f": {detail[0]}" if detail else "")
    return True, "LaTeX compilation passed"
