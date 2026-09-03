#!/usr/bin/env python3
"""Fail closed when user-visible copy in an HTML prototype degrades.

Guard card: ``.harness/guards/ui-copy-quality.md`` (project scope, static, fast).

Stable failure classes:

- ``copy.placeholder-token``   rendering leftovers such as ``undefined``, ``NaN``, ``TODO``;
- ``copy.raw-identifier``      snake_case / SCREAMING_CASE machine identifiers shown as prose
                               (outside ``<code>``, ``.mono`` or ``.hash`` containers and the lexicon
                               allowlist);
- ``copy.filler-phrase``       marketing or model-generated filler from the project lexicon;
- ``copy.developer-jargon``    implementation vocabulary that a reader of the product cannot act on;
- ``copy.mixed-script-spacing`` a CJK character glued to an ASCII letter or digit (the product
                               convention is one space between scripts);
- ``copy.doubled-word``        a two- or three-character CJK word repeated back to back
                               (``每次每次``); reported as a warning because reduplication can be
                               legitimate.

The checker looks only at strings a reader can see: text between tags and quoted JavaScript
string literals that contain CJK characters, plus ``placeholder``/``title``/``aria-label``
attributes.  Comments and CSS are never inspected.  It does not judge whether the copy is
*good*; it removes the mechanical defects a human or model review keeps missing, so the review
can spend its time on meaning.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEXICON = ROOT / "docs/quality-gates/ui-copy-lexicon.json"
DEFAULT_TARGETS = (
    ROOT / "docs/prototypes/problem-intel-console.html",
    ROOT / "docs/prototypes/review-console.html",
)

CJK = "㐀-鿿"
TAG_TEXT = re.compile(r"<(?P<tag>[a-zA-Z][a-zA-Z0-9-]*)(?P<attrs>[^<>]*)>(?P<text>[^<>]*?)(?=<)", re.DOTALL)
ATTR_TEXT = re.compile(r"\b(?:placeholder|title|aria-label|alt)=\"(?P<text>[^\"]*)\"")
JS_STRING = re.compile(r"\"(?P<text>[^\"\\\n]*[" + CJK + r"][^\"\\\n]*)\"")
STYLE_BLOCK = re.compile(r"<style>.*?</style>", re.DOTALL)
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
HAS_CJK = re.compile("[" + CJK + "]")
PLACEHOLDER = re.compile(r"\b(?:undefined|NaN|TODO|TBD|FIXME|lorem)\b|\[object Object\]")
SNAKE = re.compile(r"(?<![\w./-])[a-z][a-z0-9]*(?:_[a-z0-9]+)+(?![\w./-])")
# underscore-joined constants anywhere, or a bare all-caps word of six or more letters embedded in a CJK
# sentence (状态必须为 UNCALIBRATED); all-caps English labels such as "EXPERT REVIEW · 原型" are not leaks
SCREAMING = re.compile(r"(?<![\w./-])[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+(?![\w./-])")
EMBEDDED_CAPS = re.compile("[" + CJK + r"][^A-Za-z\n]{0,3}([A-Z]{6,})(?![A-Za-z])")
MIXED = re.compile("[" + CJK + "][A-Za-z0-9]|[A-Za-z0-9][" + CJK + "]")
DOUBLED = re.compile("([" + CJK + "]{2,3})\\1")
EXEMPT_TAGS = frozenset({"code", "kbd", "pre", "samp", "var", "script", "style"})
EXEMPT_CLASS_TOKENS = frozenset({"mono", "hash", "ev", "seq"})


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    excerpt: str
    why: str
    fix: str

    def render(self) -> str:
        return (
            f"{self.file}:{self.line}: [{self.rule}] ({self.severity}) {self.excerpt!r}\n"
            f"    why: {self.why}\n    fix: {self.fix}"
        )


@dataclass(frozen=True)
class Segment:
    line: int
    text: str
    exempt: bool


def load_lexicon(path: Path) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"lexicon root must be an object: {path}")
    lexicon: dict[str, list[str]] = {}
    for key in (
        "identifier_container_classes",
        "filler_phrases",
        "developer_jargon",
        "developer_jargon_allow_contexts",
        "allow_identifiers",
        "allow_reduplication",
    ):
        values = data.get(key, [])
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            raise ValueError(f"lexicon key {key!r} must be a list of strings")
        lexicon[key] = values
    return lexicon


def _is_exempt(tag: str, attrs: str, container_classes: frozenset[str] = EXEMPT_CLASS_TOKENS) -> bool:
    """True when the element is a declared identifier container (code-like tag or lexicon class)."""
    if tag.lower() in EXEMPT_TAGS:
        return True
    match = re.search(r"class=\"([^\"]*)\"", attrs)
    if match is None:
        return False
    tokens = set(match.group(1).replace("${", " ").split())
    return bool(tokens & container_classes)


def _line_of(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def extract_segments(source: str, container_classes: frozenset[str] = EXEMPT_CLASS_TOKENS) -> list[Segment]:
    """Return the visible-copy candidates of an HTML/JS prototype."""

    blank = lambda match: re.sub(r"[^\n]", " ", match.group(0))  # keep line numbers stable
    stripped = STYLE_BLOCK.sub(blank, source)
    stripped = BLOCK_COMMENT.sub(blank, stripped)
    segments: list[Segment] = []
    seen: set[tuple[int, str]] = set()

    def add(index: int, text: str, exempt: bool) -> None:
        cleaned = " ".join(text.split())
        if not cleaned or not HAS_CJK.search(cleaned):
            return
        key = (_line_of(stripped, index), cleaned)
        if key in seen:
            return
        seen.add(key)
        segments.append(Segment(key[0], cleaned, exempt))

    for match in TAG_TEXT.finditer(stripped):
        if match.group("tag").lower() in {"script", "style"}:
            continue  # not rendered; JavaScript string literals are collected separately below
        if '"' in match.group("text"):
            continue  # a bare double quote means the "text" is JavaScript code following an inline <br>, not rendered prose
        add(match.start("text"), match.group("text"), _is_exempt(match.group("tag"), match.group("attrs"), container_classes))
    for match in ATTR_TEXT.finditer(stripped):
        add(match.start("text"), match.group("text"), False)
    for match in JS_STRING.finditer(stripped):
        text = match.group("text")
        if "<" in text or ">" in text:
            continue  # markup fragments are covered by the tag pass
        add(match.start("text"), text, False)
    return segments


def _strip_interpolations(text: str) -> str:
    return re.sub(r"\$\{[^}]*\}", " ", text)


def check_source(path: Path, source: str, lexicon: dict[str, list[str]]) -> list[Finding]:
    findings: list[Finding] = []
    relative = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    allow_identifiers = set(lexicon["allow_identifiers"])
    allow_contexts = lexicon["developer_jargon_allow_contexts"]
    allow_reduplication = set(lexicon["allow_reduplication"])
    container_classes = EXEMPT_CLASS_TOKENS | frozenset(lexicon["identifier_container_classes"])

    for segment in extract_segments(source, container_classes):
        prose = _strip_interpolations(segment.text)
        excerpt = prose if len(prose) <= 80 else prose[:77] + "..."

        placeholder = PLACEHOLDER.search(prose)
        if placeholder:
            findings.append(Finding(relative, segment.line, "copy.placeholder-token", "error", excerpt,
                                    f"rendering leftover {placeholder.group(0)!r} would reach the reader",
                                    "render a real value or a written fallback state instead of the raw token"))

        if not segment.exempt:
            for pattern in (SNAKE, SCREAMING, EMBEDDED_CAPS):
                for identifier in pattern.findall(prose):
                    if identifier in allow_identifiers:
                        continue
                    findings.append(Finding(relative, segment.line, "copy.raw-identifier", "error", excerpt,
                                            f"machine identifier {identifier!r} is shown as prose",
                                            "translate it to product language, or wrap it in <code>/.mono when the reader must see the field name, or allowlist it in the lexicon with a reason"))

        for phrase in lexicon["filler_phrases"]:
            if phrase.lower() in prose.lower():
                findings.append(Finding(relative, segment.line, "copy.filler-phrase", "error", excerpt,
                                        f"filler phrase {phrase!r} makes a claim without an object or a fact",
                                        "say what the feature does to which object with which result, or delete the sentence"))

        for term in lexicon["developer_jargon"]:
            if term in prose and not any(context in prose for context in allow_contexts):
                findings.append(Finding(relative, segment.line, "copy.developer-jargon", "error", excerpt,
                                        f"implementation vocabulary {term!r} reached user-facing copy",
                                        "name the thing the reader can see or do (e.g. 服务器 / 已连接 / 是否), or add an allow context to the lexicon"))

        mixed = MIXED.search(prose)
        if mixed:
            findings.append(Finding(relative, segment.line, "copy.mixed-script-spacing", "error", excerpt,
                                    f"{mixed.group(0)!r} glues CJK to ASCII without the project's spacing convention",
                                    "insert one space between the CJK and the ASCII run"))

        doubled = DOUBLED.search(prose)
        if doubled and doubled.group(0) not in allow_reduplication:
            findings.append(Finding(relative, segment.line, "copy.doubled-word", "warning", excerpt,
                                    f"{doubled.group(0)!r} repeats a word back to back; usually a typo",
                                    "delete the duplicate, or allowlist the reduplication in the lexicon"))
    return findings


def check_files(paths: list[Path], lexicon: dict[str, list[str]]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(Finding(str(path), 0, "copy.unreadable-source", "error", "",
                                    f"cannot read {path}: {exc}", "fix the path or file encoding"))
            continue
        findings.extend(check_source(path, source, lexicon))
    return findings


def write_evidence(directory: Path, findings: list[Finding], targets: list[Path], lexicon_path: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    payload = {
        "guard": "ui-copy-quality",
        "status": "FAIL" if errors else "PASS",
        "lexicon": str(lexicon_path.relative_to(ROOT)) if lexicon_path.is_relative_to(ROOT) else str(lexicon_path),
        "targets": [str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p) for p in targets],
        "error_count": len(errors),
        "warning_count": len(warnings),
        "findings": [asdict(f) for f in findings],
    }
    (directory / "ui-copy-quality.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [f"# ui-copy-quality: {payload['status']}", "", f"- errors: {len(errors)}", f"- warnings: {len(warnings)}", ""]
    lines += [f.render() for f in findings] or ["No findings."]
    (directory / "ui-copy-quality.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("targets", nargs="*", type=Path, help="HTML prototypes to scan (default: the console and review prototypes)")
    parser.add_argument("--lexicon", type=Path, default=DEFAULT_LEXICON)
    parser.add_argument("--evidence-dir", type=Path, help="write ui-copy-quality.{json,md} here")
    parser.add_argument("--warnings-as-errors", action="store_true")
    args = parser.parse_args(argv)
    targets = [p.resolve() for p in (args.targets or list(DEFAULT_TARGETS))]
    try:
        lexicon = load_lexicon(args.lexicon)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ui-copy-quality: FAIL\n- cannot load lexicon: {exc}", file=sys.stderr)
        return 1
    findings = check_files(targets, lexicon)
    if args.evidence_dir:
        write_evidence(args.evidence_dir, findings, targets, args.lexicon)
    errors = [f for f in findings if f.severity == "error" or args.warnings_as_errors]
    warnings = [f for f in findings if f.severity == "warning" and not args.warnings_as_errors]
    for finding in warnings:
        print(finding.render())
    if errors:
        print("ui-copy-quality: FAIL", file=sys.stderr)
        for finding in errors:
            print(finding.render(), file=sys.stderr)
        print("Repair: rewrite the copy for a reader who sees only the screen; the lexicon is the place for deliberate exceptions.", file=sys.stderr)
        return 1
    print(f"ui-copy-quality: PASS ({len(targets)} file(s), {len(warnings)} warning(s); lexical checks only, not a review of meaning)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
