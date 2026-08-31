from __future__ import annotations

import unittest
from pathlib import Path


class ConsolePrototypeTests(unittest.TestCase):
    def test_bridge_has_explicit_provenance_and_memory_only_review_token(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        self.assertIn('const endpoints = url ? [url] : ["console.json", "/api/console"]', page)
        self.assertIn('id = "console-provenance"', page)
        self.assertIn("new EventSource", page)
        self.assertIn('url.searchParams.set("after", String(cursor))', page)
        self.assertIn('tokenInput.type !== "password"', page)
        self.assertIn('tokenInput.value = ""', page)
        bridge = page.split("const ConsoleBridge", 1)[1]
        self.assertNotIn("localStorage", bridge)
        self.assertNotIn("sessionStorage", bridge)

    def test_live_views_replace_only_declared_console_contract_surfaces(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        for view in ('"source"', '"dag"', '"proofchain"', '"tools"', '"reasoning"', '"admin_roles"', '"campaign"'):
            self.assertIn(view, page)
        self.assertIn("payload.view_contract", page)
        self.assertIn('"/api/console"', page)

    def test_source_links_allow_only_web_schemes(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        self.assertIn("const safeExternalHref", page)
        self.assertIn("/^(https?):$/.test(parsed.protocol)", page)
        self.assertIn("const sourceCell = item", page)
        self.assertNotIn('href="${liveEsc(item.canonical_uri)}"', page)

    def test_mobile_topbar_keeps_console_provenance_visible(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        self.assertIn("#console-provenance{order:2", page)
        self.assertIn(".topbar{height:auto", page)


if __name__ == "__main__":
    unittest.main()
