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
from matharc.v02.workers import StaticProposalWorker
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_bundle import write_full_workspace_bundle


class ConsolePrototypeTests(unittest.TestCase):
    def test_browser_title_uses_the_product_name_not_the_internal_plane_name(self) -> None:
        page = (
            Path(__file__).resolve().parents[1]
            / "docs/prototypes/problem-intel-console.html"
        ).read_text(encoding="utf-8")
        self.assertIn("<title>MathArc 数学研究工作台</title>", page)
        self.assertNotIn("<title>问题情报平面控制台</title>", page)

    def test_browser_gate_runs_campaign_through_cli_and_asserts_sse_dom_refresh(self) -> None:
        gate = (Path(__file__).resolve().parents[1] / "scripts/console_browser_gate.mjs").read_text(encoding="utf-8")
        self.assertIn('"-m", "matharc.v02.cli", "run"', gate)
        self.assertNotIn("ResearchCampaign", gate)
        self.assertIn("M1 SSE refresh did not render the newly emitted event", gate)

    def test_browser_gate_covers_mobile_viewports_and_real_keyboard_activation(self) -> None:
        gate = (Path(__file__).resolve().parents[1] / "scripts/console_browser_gate.mjs").read_text(encoding="utf-8")
        self.assertIn('{ name: "mobile-390", width: 390, height: 844 }', gate)
        self.assertIn('{ name: "mobile-820", width: 820, height: 1180 }', gate)
        self.assertIn("isMobile: true", gate)
        self.assertIn('page.keyboard.press("Enter")', gate)
        self.assertIn('page.keyboard.press("Space")', gate)
        self.assertIn("tabindex disclosure control", gate)

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
        self.assertIn('admin_roster: {n:"评审名册",     b:()=>S.consolePayload ||', page)
        self.assertIn('novelty:["novelty_projection","live_if_configured"]', page)
        self.assertIn("const validateLiveNovelty", page)

    def test_routes_and_disclosure_have_live_renderers_and_fail_closed_fallback(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        live_section = page[page.index("const DEMO_VIEWS ="):page.index("/* M2 reads only the review service.")]
        self.assertIn("V.routes = () =>", live_section)
        self.assertIn("V.disclosure = () =>", live_section)
        self.assertIn('projectionUnavailable("路线与证伪"', live_section)
        self.assertIn('projectionUnavailable("分级披露"', live_section)
        self.assertIn("payload.routes", live_section)
        self.assertIn("payload.disclosure", live_section)

    def test_loaded_export_without_route_disclosure_projection_fails_closed(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is required for the projection boundary regression")
        script = textwrap.dedent(
            r"""
            const fs = require("fs");
            const vm = require("vm");
            const page = fs.readFileSync(process.argv[1], "utf8");
            const start = page.indexOf("const projectionUnavailable =");
            const end = page.indexOf("/* M2 reads only the review service.", start);
            if (start < 0 || end < 0) throw new Error("projection renderer source was not found");
            const context = {
              S: { consolePayload: { routes: null, disclosure: null } },
              V: { routes: () => ({ task: "DEMO-routes" }), disclosure: () => ({ task: "DEMO-disclosure" }) },
              DEMO_VIEWS: { routes: () => ({ task: "DEMO-routes" }), disclosure: () => ({ task: "DEMO-disclosure" }) },
              livePayloadFor: () => null,
              liveCard: (...values) => values.join("|"), liveEsc: value => String(value),
              card: (...values) => values.join("|"), split: (...values) => values.join("|"),
              liveEnumPill: () => "", liveEnumText: () => "",
              Math, String,
            };
            vm.runInNewContext(page.slice(start, end), context);
            for (const view of ["routes", "disclosure"]) {
              const result = context.V[view]();
              if (!result.task.includes("实时投影不可用") || result.task.includes("DEMO-")) {
                throw new Error(`${view} rendered demo data after a loaded export lost its projection`);
              }
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

    def test_novelty_live_renderer_has_no_demo_protocol_fallback_when_export_loaded(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        start = page.index('V.novelty = () => {', page.index('const DEMO_VIEWS ='))
        end = page.index('/* M2 reads only', start)
        live_source = page[start:end]
        self.assertNotIn("SEARCH_PROTO", live_source)
        self.assertIn("实时投影不可用", live_source)
        self.assertIn("缺少已验证的 novelty audit projection", live_source)

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
            const names = [
              "campaign", "topics", "portfolio", "dossier", "frontier", "difficulty", "admin_users", "admin_upstream",
              "admin_roster", "admin_cost", "acct_overview", "acct_usage", "acct_billing", "acct_limits",
            ];
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

    def test_research_preview_access_uses_same_origin_json_contracts(self) -> None:
        page = (Path(__file__).resolve().parents[1] / "docs/prototypes/problem-intel-console.html").read_text(encoding="utf-8")
        access = page[page.index("const AccessConsole = (() => {"):page.index('document.addEventListener("click"', page.index("const AccessConsole = (() => {"))]
        self.assertIn('fetch("/api/access/redeem"', access)
        self.assertIn('fetch("/api/access/applications"', access)
        self.assertIn('fetch("/api/access/session"', access)
        self.assertIn('fetch("/api/access/logout"', access)
        self.assertEqual(access.count('credentials:"same-origin"'), 4)
        self.assertIn('JSON.stringify({email, code})', access)
        self.assertIn("research_role:(S.access.researchRole", access)
        self.assertIn("research_direction:(S.access.researchDirection", access)
        self.assertIn('payload.authenticated === true', access)
        self.assertIn('payload.application.status === "PENDING"', access)
        self.assertIn('response.status !== 202', access)
        self.assertIn('type="password"', page)
        self.assertIn('autocomplete="one-time-code"', page)
        self.assertNotIn("演示动作：已进入控制台", page)
        self.assertNotIn('guest:false', page)
        self.assertLess(access.index('fetch("/api/access/redeem"'), access.index('codeInput.value = ""'))
        self.assertLess(access.index('codeInput.value = ""'), access.index("const response = await request"))

    def test_access_controller_fails_closed_and_keeps_applications_pending(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is required for the access-controller regression")
        script = textwrap.dedent(
            r"""
            const fs = require("fs");
            const vm = require("vm");
            const page = fs.readFileSync(process.argv[1], "utf8");
            const start = page.indexOf("const AccessConsole = (() => {");
            const end = page.indexOf('document.addEventListener("click"', start);
            if (start < 0 || end < 0) throw new Error("access controller source was not found");

            const elements = {
              "f-mail": { value: "researcher@example.edu", focus() {} },
              "f-code": { value: "MA-2026-VALID" },
            };
            const requests = [];
            const S = {
              guest: true, view: "login", plane: "p",
              access: {
                mode: "redeem", email: "", institution: "", researchRole: "", researchDirection: "", purpose: "",
                redeemStatus: "idle", redeemMessage: "", applicationStatus: "idle", applicationMessage: "", logoutStatus: "idle", session: null,
              },
            };
            let renderCount = 0;
            const context = {
              S,
              $: selector => elements[selector.slice(1)] || null,
              fetch(url, options) {
                return new Promise((resolve, reject) => requests.push({ url, options, resolve, reject }));
              },
              render() { renderCount += 1; },
              toast() {},
              ConsoleBridge: { async loadExport() { renderCount += 1; return true; }, connectEvents() {}, clear() {} },
              window: { scrollTo() {} },
              setTimeout(handler) { handler(); },
            };
            vm.runInNewContext(page.slice(start, end) + ";this.AccessConsole = AccessConsole;", context);
            const response = (status, payload) => ({
              ok: status >= 200 && status < 300,
              status,
              json: async () => payload,
            });
            const flush = () => new Promise(resolve => setImmediate(resolve));

            (async () => {
              const redeem = context.AccessConsole.redeem();
              if (requests.length !== 1) throw new Error("redeem request was not started");
              if (elements["f-code"].value !== "") throw new Error("invite code remained in the DOM after submission");
              if (!S.guest || S.access.redeemStatus !== "loading") throw new Error("loading state entered an authenticated console");
              const redeemRequest = requests[0];
              if (redeemRequest.url !== "/api/access/redeem") throw new Error("wrong redeem endpoint");
              if (redeemRequest.options.credentials !== "same-origin") throw new Error("redeem omitted same-origin credentials");
              const redeemBody = JSON.parse(redeemRequest.options.body);
              if (redeemBody.email !== "researcher@example.edu" || redeemBody.code !== "MA-2026-VALID") throw new Error("wrong redeem payload");
              redeemRequest.resolve(response(200, {
                authenticated: true,
                session: { email: "researcher@example.edu", topic_scopes: ["combinatorics"], expires_at: 1800003600 },
              }));
              if (!(await redeem)) throw new Error("valid authenticated session was rejected");
              if (S.guest || S.view !== "portfolio" || !S.access.session) throw new Error("valid session did not enter the console");

              S.guest = true;
              S.view = "login";
              S.access.session = null;
              S.access.redeemStatus = "idle";
              elements["f-code"].value = "MA-2026-MALFORMED";
              const malformed = context.AccessConsole.redeem();
              requests[1].resolve(response(200, { authenticated: true, session: { email: "researcher@example.edu" } }));
              if (await malformed) throw new Error("malformed authenticated session was accepted");
              if (!S.guest || S.view !== "login" || S.access.session) throw new Error("malformed session crossed the guest boundary");
              if (!S.access.redeemMessage.includes("无法确认的会话")) throw new Error("malformed session error was not shown");

              S.access.mode = "application";
              Object.assign(S.access, {
                email: "applicant@example.edu", institution: "Example University", researchRole: "doctoral researcher",
                researchDirection: "combinatorics", purpose: "Evaluate governed proof workflows", applicationStatus: "idle",
              });
              const application = context.AccessConsole.submitApplication();
              if (requests.length !== 3) throw new Error("application request was not started");
              const applicationRequest = requests[2];
              if (applicationRequest.url !== "/api/access/applications" || applicationRequest.options.credentials !== "same-origin") {
                throw new Error("application request did not use the same-origin endpoint");
              }
              const applicationBody = JSON.parse(applicationRequest.options.body);
              for (const field of ["email", "institution", "research_role", "research_direction", "purpose"]) {
                if (!applicationBody[field]) throw new Error(`application omitted ${field}`);
              }
              applicationRequest.resolve(response(202, {
                application: {
                  application_id: "APP-1", status: "PENDING", email: "applicant@example.edu", submitted_at: 1800000000,
                },
              }));
              if (!(await application)) throw new Error("valid pending application was rejected");
              if (!S.guest || S.view !== "login" || S.access.session) throw new Error("pending application entered the console");
              if (S.access.applicationStatus !== "success" || !S.access.applicationMessage.includes("待审核")) {
                throw new Error("pending application status was not shown");
              }

              S.guest = false;
              S.view = "portfolio";
              S.access.session = { email: "researcher@example.edu", topic_scopes: ["combinatorics"], expires_at: 1800003600 };
              const logout = context.AccessConsole.logout();
              if (requests[3].url !== "/api/access/logout" || requests[3].options.method !== "POST") throw new Error("logout request was not sent");
              requests[3].resolve(response(204, null));
              if (!(await logout) || !S.guest || S.view !== "landing" || S.access.session) throw new Error("confirmed logout did not clear the session");

              S.view = "login";
              const restore = context.AccessConsole.restoreSession();
              if (requests[4].url !== "/api/access/session" || requests[4].options.method !== "GET") throw new Error("session restore request was not sent");
              requests[4].resolve(response(200, {
                authenticated: true,
                session: { email: "restored@example.edu", topic_scopes: [], expires_at: 1800003600 },
              }));
              if (!(await restore) || S.guest || S.view !== "portfolio") throw new Error("validated session was not restored");
              await flush();
              if (renderCount < 9) throw new Error("access states were not rendered");
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
