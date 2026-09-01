from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from matharc.v02.budget import BudgetLedger
from matharc.v02.campaign import ResearchCampaign
from matharc.v02.console_export import build_console_export
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workers import StaticProposalWorker


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
        self.assertIn("canonical_unsigned_json", page)
        self.assertIn("S.consolePayload = null", page)
        self.assertIn("latestLoad", page)
        self.assertIn("same-origin /api/review service", page)

    def test_configured_console_never_substitutes_demo_for_unconfigured_local_views(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is required for the local projection boundary regression")
        script = textwrap.dedent(
            r"""
            const fs = require("fs");
            const vm = require("vm");
            const page = fs.readFileSync(process.argv[1], "utf8");
            const start = page.indexOf("/* Local-completion projections");
            const end = page.indexOf("window.MathArcConsole", start);
            if (start < 0 || end < 0) throw new Error("local projection source was not found");
            const names = ["campaign", "topics", "portfolio", "dossier", "frontier", "difficulty", "admin_users", "admin_upstream"];
            const V = Object.fromEntries(names.map(name => [name, () => ({ task: `DEMO-${name}` })]));
            const local_console = Object.fromEntries([
              "workspace_index", "exploration_sessions", "topic_portfolio", "candidate_problems", "difficulty_ledger", "operations",
            ].map(key => [key, { state: "not_configured" }]));
            const context = {
              S: { consolePayload: { local_console } }, V,
              liveCard: (...values) => values.join("|"), liveEsc: value => String(value),
            };
            vm.runInNewContext(page.slice(start, end), context);
            for (const name of names.slice(1)) {
              const task = context.V[name]().task;
              if (!task.includes("未配置") || task.includes(`DEMO-${name}`)) {
                throw new Error(`${name} substituted a demo for a configured not_configured projection`);
              }
            }
            if (context.V.campaign().task !== "DEMO-campaign") {
              throw new Error("campaign did not preserve its existing registered-report projection");
            }
            """
        )
        completed = subprocess.run(
            [node, "-e", script, str(Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_registered_campaign_export_renders_live_report_not_demo(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is required for the embedded live campaign regression")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            write_full_workspace_bundle(root)
            workspace = ResearchWorkspace.load(root)
            campaign = ResearchCampaign(
                workspace.trace,
                [StaticProposalWorker("prover", {})],
                budget=BudgetLedger(wall_seconds_limit=0.0),
            )
            workspace.record_campaign_result(campaign, campaign.run())
            workspace.save()
            payload = build_console_export(root)
            self.assertEqual(
                payload["view_contract"]["campaign_observatory"],
                "live_if_current_workspace_campaign_is_registered",
            )
            self.assertTrue(payload["campaign"]["available"])
            script = textwrap.dedent(
                r"""
                const fs = require("fs");
                const vm = require("vm");
                const page = fs.readFileSync(process.argv[1], "utf8");
                const payload = JSON.parse(process.argv[2]);
                const start = page.indexOf("const DEMO_VIEWS =");
                const end = page.indexOf("/* Console transport", start);
                if (start < 0 || end < 0) throw new Error("live view source was not found");
                const context = {
                  S: { consolePayload: payload },
                  V: { campaign: () => ({ task: "DEMO_CAMPAIGN" }) },
                  esc(value) { return String(value); },
                  card(title, subtitle, body) { return `${title}|${subtitle}|${body}`; },
                };
                vm.runInNewContext(page.slice(start, end) + ";this.renderCampaign = () => V.campaign();", context);
                const rendered = context.renderCampaign();
                if (!rendered.task.includes("真实报告")) throw new Error("registered campaign fell back to the demo renderer");
                const text = String(rendered.main);
                if (!text.includes("发布状态已终止：已证明且审计通过")) throw new Error("registered campaign report was not rendered with a mapped release state");
                if (text.includes("release_state_terminal:") || text.includes("PROVED_AND_AUDITED")) throw new Error("raw campaign release tokens leaked into the UI");
                """
            )
            completed = subprocess.run(
                [
                    node,
                    "-e",
                    script,
                    str(Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html"),
                    json.dumps(payload),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_source_links_allow_only_web_schemes(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        self.assertIn("const safeExternalHref", page)
        self.assertIn("/^(https?):$/.test(parsed.protocol)", page)
        self.assertIn("const sourceCell = item", page)
        self.assertNotIn('href="${liveEsc(item.canonical_uri)}"', page)

    def test_live_machine_tokens_have_non_echoing_ui_maps(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        self.assertIn('event_type: Object.freeze', page)
        self.assertIn('release_state: Object.freeze', page)
        self.assertIn('campaign_reason: Object.freeze', page)
        self.assertIn('liveEnumPill("event_type", row.event.event_type)', page)
        self.assertNotIn('liveEsc(row.event.event_type)', page)
        self.assertNotIn('发布状态已终止 (${text})', page)
        self.assertNotIn('liveEsc(campaign.reason)', page)

    def test_mobile_topbar_keeps_console_provenance_visible(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        self.assertIn("#console-provenance{order:2", page)
        self.assertIn(".topbar{height:auto", page)
        self.assertIn('setAttribute("aria-live", "polite")', page)

    def test_bridge_rejects_stale_loads_and_reconnects_on_generation_reset(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is required for the embedded bridge regression")
        script = textwrap.dedent(
            r"""
            const fs = require("fs");
            const vm = require("vm");
            const page = fs.readFileSync(process.argv[1], "utf8");
            const start = page.indexOf("const ConsoleBridge = (() => {");
            const endMarker = "window.MathArcConsole = ConsoleBridge;";
            const end = page.indexOf(endMarker, start);
            if (start < 0 || end < 0) throw new Error("bridge source was not found");

            class Element {
              constructor() { this.dataset = {}; this.id = ""; this.textContent = ""; }
              setAttribute() {}
              focus() {}
            }
            class InputElement extends Element {}
            class EventSourceStub {
              static instances = [];
              constructor(url) {
                this.url = url;
                this.closed = false;
                this.handlers = {};
                EventSourceStub.instances.push(this);
              }
              addEventListener(name, handler) { this.handlers[name] = handler; }
              close() { this.closed = true; }
              fail() { if (this.onerror) this.onerror(); }
            }

            const timers = [];
            let nextTimerId = 0;
            const window = {
              location: { href: "https://example.test/console.html" },
              setTimeout(handler, delay) {
                const timer = { id: ++nextTimerId, handler, delay, cancelled: false };
                timers.push(timer);
                return timer.id;
              },
              clearTimeout(id) {
                const timer = timers.find(item => item.id === id);
                if (timer) timer.cancelled = true;
              },
            };
            const topbar = { inserted: [], insertBefore(element) { this.inserted.push(element); } };
            const document = {
              activeElement: null,
              createElement() { return new Element(); },
              querySelector(selector) { return selector === ".topbar" ? topbar : null; },
              getElementById() { return null; },
              querySelectorAll() { return []; },
            };
            const requests = [];
            let renderCount = 0;
            const context = {
              console,
              document,
              Element,
              HTMLElement: Element,
              HTMLInputElement: InputElement,
              EventSource: EventSourceStub,
              URL,
              window,
              fetch(url) {
                return new Promise((resolve, reject) => requests.push({ url, resolve, reject }));
              },
              S: { consolePayload: null },
              render() { renderCount += 1; },
              toast() {},
            };
            vm.runInNewContext(page.slice(start, end) + endMarker, context);
            const bridge = context.window.MathArcConsole;
            const response = payload => ({ ok: true, json: async () => payload });
            const payload = (runId, count) => ({
              schema_version: "1.0",
              provenance: { run_id: runId, state_digest_sha256: runId + "-state", event_head_hash: runId + "-head" },
              workspace: { events: { events: Array.from({ length: count }, (_, sequence) => ({ sequence })) } },
              view_contract: {},
              role_policy: {},
              campaign: {},
            });
            const flush = () => new Promise(resolve => setImmediate(resolve));
            const runNextTimer = () => {
              const timer = timers.find(item => !item.cancelled);
              if (!timer) throw new Error("expected a scheduled reconnect");
              timer.cancelled = true;
              timer.handler();
            };

            (async () => {
              const staleLoad = bridge.loadExport("/api/console");
              const latestLoad = bridge.loadExport("/api/console");
              if (requests.length !== 2) throw new Error("expected two concurrent loads");
              requests[1].resolve(response(payload("current", 8)));
              if (!(await latestLoad)) throw new Error("latest load was rejected");
              requests[0].resolve(response(payload("stale", 100)));
              if (await staleLoad) throw new Error("stale load was accepted");
              if (context.S.consolePayload.provenance.run_id !== "current") throw new Error("stale load mutated memory");
              if (topbar.inserted[0].textContent !== "已接入工作区 current · current-stat" || topbar.inserted[0].dataset.source !== "export") throw new Error("stale load mutated the provenance view");
              if (renderCount !== 1) throw new Error("stale load mutated the view");

              if (!bridge.connectEvents("/events")) throw new Error("initial event connection failed");
              if (!EventSourceStub.instances[0].url.endsWith("/events?after=7")) throw new Error("initial cursor was not preserved");

              const rebuiltLoad = bridge.loadExport("/api/console");
              requests[2].resolve(response(payload("rebuilt", 1)));
              if (!(await rebuiltLoad)) throw new Error("rebuilt workspace load failed");
              if (!EventSourceStub.instances[0].closed) throw new Error("old generation stream stayed open");
              if (!EventSourceStub.instances[1].url.endsWith("/events?after=0")) throw new Error("generation reset kept the old cursor");

              const advanceLoad = bridge.loadExport("/api/console");
              requests[3].resolve(response(payload("rebuilt", 6)));
              if (!(await advanceLoad)) throw new Error("same-generation update failed");
              const restartLoad = bridge.loadExport("/api/console");
              requests[4].resolve(response(payload("rebuilt", 1)));
              if (!(await restartLoad)) throw new Error("same-generation restart load failed");
              if (!EventSourceStub.instances[1].closed) throw new Error("sequence restart kept the old stream");
              if (!EventSourceStub.instances[2].url.endsWith("/events?after=0")) throw new Error("sequence restart kept the old cursor");

              EventSourceStub.instances[2].fail();
              runNextTimer();
              await flush();
              if (!EventSourceStub.instances[3].url.endsWith("/events?after=0")) throw new Error("normal reconnect did not use the current cursor");
            })().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
            """
        )
        completed = subprocess.run(
            [node, "-e", script, str(Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
