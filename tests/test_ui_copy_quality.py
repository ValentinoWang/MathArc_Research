from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def _load_guard() -> ModuleType:
    path = ROOT / "scripts/check_ui_copy_quality.py"
    spec = importlib.util.spec_from_file_location("ui_copy_quality_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve string annotations through sys.modules
    spec.loader.exec_module(module)
    return module


GUARD = _load_guard()
LEXICON = GUARD.load_lexicon(GUARD.DEFAULT_LEXICON)


def _rules(source: str) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "page.html"
        path.write_text(source, encoding="utf-8")
        return [finding.rule for finding in GUARD.check_source(path, source, LEXICON)]


class UiCopyQualityGuardTests(unittest.TestCase):
    def test_green_current_prototypes_have_no_errors(self) -> None:
        findings = GUARD.check_files(list(GUARD.DEFAULT_TARGETS), LEXICON)
        errors = [finding.render() for finding in findings if finding.severity == "error"]
        self.assertEqual(errors, [])

    def test_red_raw_identifier_in_prose_fails(self) -> None:
        self.assertIn("copy.raw-identifier", _rules('<p class="note">身份提供方为 not_configured。</p>'))
        self.assertIn("copy.raw-identifier", _rules('<script>toast("状态必须为 UNCALIBRATED");</script>'))

    def test_green_identifier_inside_declared_containers_or_allowlist_passes(self) -> None:
        self.assertEqual(_rules('<p class="note">字段 <span class="mono">event_sequence</span> 决定范围。</p>'), [])
        self.assertEqual(_rules('<code>not_configured 表示未配置</code>'), [])
        self.assertEqual(_rules('<span class="hint">名册中的 reviewer_id</span>'), [])

    def test_red_placeholder_token_and_filler_fail(self) -> None:
        self.assertIn("copy.placeholder-token", _rules('<p>当前值：undefined 条记录</p>'))
        self.assertIn("copy.filler-phrase", _rules('<p>一站式赋能数学研究</p>'))

    def test_red_developer_jargon_fails_unless_allowed_context(self) -> None:
        self.assertIn("copy.developer-jargon", _rules('<p class="hint">只有服务端确认会话后才会进入。</p>'))
        self.assertEqual(_rules('<p class="note">尚未声明结构化证伪测试；不会由前端补造执行结果。</p>'), [])

    def test_red_mixed_script_spacing_fails(self) -> None:
        self.assertIn("copy.mixed-script-spacing", _rules('<p>第7轮被拒绝</p>'))
        self.assertEqual(_rules('<p>第 7 轮被拒绝</p>'), [])

    def test_doubled_word_is_a_warning_and_reduplication_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            source = '<p>每次每次攻克开始前先落一条预测。</p><p>一步一步地核对。</p>'
            path.write_text(source, encoding="utf-8")
            findings = GUARD.check_source(path, source, LEXICON)
        self.assertEqual([(f.rule, f.severity) for f in findings], [("copy.doubled-word", "warning")])

    def test_comments_and_styles_are_ignored_and_line_numbers_stay_stable(self) -> None:
        source = '<style>\n.a{}\n</style>\n<script>\n/* 服务端 注释\n跨行 */\nconst x = "服务端确认";\n</script>'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_text(source, encoding="utf-8")
            findings = GUARD.check_source(path, source, LEXICON)
        self.assertEqual([(f.rule, f.line) for f in findings], [("copy.developer-jargon", 7)])

    def test_invalid_lexicon_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lexicon = Path(directory) / "lexicon.json"
            lexicon.write_text(json.dumps({"filler_phrases": "赋能"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                GUARD.load_lexicon(lexicon)

    def test_cli_writes_evidence_and_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.html"
            bad.write_text('<p>状态为 not_configured</p>', encoding="utf-8")
            evidence = Path(directory) / "quality-gates"
            self.assertEqual(GUARD.main([str(bad), "--evidence-dir", str(evidence)]), 1)
            payload = json.loads((evidence / "ui-copy-quality.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(payload["error_count"], 1)
            self.assertEqual(GUARD.main([]), 0)


if __name__ == "__main__":
    unittest.main()
