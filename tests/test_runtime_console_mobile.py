from __future__ import annotations

import re
import unittest
from pathlib import Path


class RuntimeConsoleMobileBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.page = (cls.root / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        cls.browser_gate = (cls.root / "scripts/console_browser_gate.mjs").read_text(encoding="utf-8")

    def test_mobile_shell_and_topbar_have_stable_single_column_rules(self) -> None:
        mobile = self.page[self.page.index("@media (max-width:820px)"):]
        self.assertIn(".shell,.shell.nosd{grid-template-columns:minmax(0,1fr);}", mobile)
        self.assertIn("#console-provenance{order:2", mobile)
        self.assertIn(".nowtask{order:4;flex:1 1 100%;", mobile)
        self.assertIn(".planes{order:3;flex:1 1 100%;", mobile)

    def test_auth_dom_is_invitation_first_and_fail_closed(self) -> None:
        self.assertIn('id="f-code" type="password"', self.page)
        self.assertIn('autocomplete="one-time-code"', self.page)
        self.assertIn('fetch("/api/access/redeem"', self.page)
        self.assertIn('credentials:"same-origin"', self.page)
        self.assertIn('payload.authenticated === true', self.page)
        self.assertIn("没有邀请码？申请研究预览", self.page)
        self.assertIn("审核通过前不会开通控制台访问", self.page)

    def test_mobile_browser_gate_checks_viewport_overflow_and_keyboard_flow(self) -> None:
        self.assertIn('{ name: "mobile-390", width: 390, height: 844 }', self.browser_gate)
        self.assertIn('{ name: "mobile-820", width: 820, height: 1180 }', self.browser_gate)
        self.assertIn("isMobile: true", self.browser_gate)
        self.assertRegex(self.browser_gate, re.compile(r"document\.documentElement\.scrollWidth\s*<=\s*window\.innerWidth"))
        self.assertIn('page.keyboard.press("Enter")', self.browser_gate)
        self.assertIn('page.keyboard.press("Space")', self.browser_gate)

    def test_provenance_status_remains_dom_visible_on_mobile(self) -> None:
        self.assertIn('provenance.id = "console-provenance"', self.page)
        self.assertIn('id="runtime-meta" role="status" aria-live="polite"', self.page)
        self.assertIn('id="view-data-boundary" role="status" aria-live="polite"', self.page)
        self.assertIn('setAttribute("aria-live", "polite")', self.page)

    def test_runtime_meta_has_bounded_mobile_layout_and_structured_state(self) -> None:
        self.assertIn('#runtime-meta{max-width:min(38vw,430px);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}', self.page)
        self.assertIn('#runtime-meta{order:5;flex:1 1 100%;max-width:none;overflow-wrap:anywhere;white-space:normal;}', self.page)
        self.assertIn('runtimeMeta.dataset.runtimeRunId = info.runId', self.page)
        self.assertIn('runtimeMeta.dataset.generation = info.generationId', self.page)
        self.assertNotIn('${run.budget || "未登记"}', self.page)
        self.assertNotIn('${state.candidates && Object.keys(state.candidates).length}', self.page)


if __name__ == "__main__":
    unittest.main()
