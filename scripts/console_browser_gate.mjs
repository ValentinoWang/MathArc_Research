#!/usr/bin/env node
/*
 * Guard card: console-prototype-browser-regression
 * Failure class: a browser-rendered console view diverges from the declared
 * prototype contract (broken render, responsive imbalance, falsified ledger,
 * inaccessible in-place disclosure, or a lost data-origin boundary).
 * Scope: docs/prototypes/problem-intel-console.html only; this does not prove
 * authenticated production behaviour. Repair: update the prototype and this
 * case list together when a deliberately approved view contract changes.
 */
import { createRequire } from "node:module";
import { execFileSync, spawn, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const require = createRequire(import.meta.url);
const ROOT = resolve(import.meta.dirname, "..");
const PAGE_PATH = resolve(ROOT, "docs/prototypes/problem-intel-console.html");
const PAGE_SOURCE = readFileSync(PAGE_PATH, "utf8");
const BLUEPRINT_PATH = resolve(ROOT, "docs/prototypes/console-dev-blueprint.html");
const BLUEPRINT_SOURCE = readFileSync(BLUEPRINT_PATH, "utf8");
const WIDTHS = [1240, 1366, 1440, 1536, 1728, 1920];
const MOBILE_VIEWPORTS = [
  { name: "mobile-390", width: 390, height: 844 },
  { name: "mobile-820", width: 820, height: 1180 },
];
const CAMPAIGNS = ["c7", "q6"];
const LIVE_VIEWS = new Set(["source", "dag", "proofchain", "tools", "reasoning", "admin_roles", "campaign", "routes", "disclosure", "novelty"]);
const PROCESS_SCOPED = new Set([
  "campaign", "exploration", "conjecture", "routes", "dag", "proofchain", "tools", "reasoning", "novelty", "disclosure",
]);
const FAIL_CLOSED_M2_VIEWS = new Set(["admin_roster", "admin_cost", "acct_overview", "acct_usage", "acct_billing", "acct_limits"]);

const VIEW_CASES = [
  ...[
    "portfolio", "dossier", "cert", "frontier", "radar", "source", "novelty", "difficulty", "dag", "disclosure",
    "campaigns", "campaign", "exploration", "conjecture", "routes", "tools", "reasoning", "landing", "login",
    "acct_overview", "acct_usage", "acct_billing", "acct_limits", "admin_cost", "admin_upstream", "admin_users",
    "field", "topics", "admin_roles", "admin_roster", "admin_queue", "proofchain",
  ].map(view => ({ name: view, view })),
  { name: "source-observation-o1", view: "source", action: ["obs", { id: "o1" }] },
  { name: "source-observation-o3", view: "source", action: ["obs", { id: "o3" }] },
  { name: "dossier-version-1", view: "dossier", action: ["ver", { i: "1" }] },
  { name: "dossier-version-2", view: "dossier", action: ["ver", { i: "2" }] },
  { name: "dossier-version-3", view: "dossier", action: ["ver", { i: "3" }] },
  { name: "frontier-node-n7", view: "frontier", action: ["fnode", { id: "n7" }] },
  { name: "frontier-node-barrier", view: "frontier", action: ["fnode", { id: "barrier" }] },
  { name: "campaign-round-1", view: "campaign", action: ["round", { i: "0" }] },
  { name: "campaign-round-3", view: "campaign", action: ["round", { i: "2" }] },
  { name: "campaign-round-7", view: "campaign", action: ["round", { i: "6" }] },
  { name: "exploration-e1", view: "exploration", action: ["expl", { i: "0" }] },
  { name: "exploration-e2", view: "exploration", action: ["expl", { i: "1" }] },
  { name: "conjecture-c1", view: "conjecture", action: ["conj", { i: "0" }] },
  { name: "conjecture-c2", view: "conjecture", action: ["conj", { i: "1" }] },
  { name: "routes-r1", view: "routes", action: ["rt", { i: "0" }] },
  { name: "routes-r2", view: "routes", action: ["rt", { i: "1" }] },
  { name: "tools-call-1", view: "tools", action: ["tool", { i: "0" }] },
  { name: "tools-call-4", view: "tools", action: ["tool", { i: "3" }] },
  { name: "reasoning-step-1", view: "reasoning", action: ["rsn", { i: "0" }] },
  { name: "reasoning-step-2", view: "reasoning", action: ["rsn", { i: "1" }] },
];

function fail(message) {
  throw new Error(`console browser gate: ${message}`);
}

function assert(condition, message) {
  if (!condition) fail(message);
}

assert(BLUEPRINT_SOURCE.includes("console_routes_projection"), "blueprint missing live routes projection contract");
assert(BLUEPRINT_SOURCE.includes("console_disclosure_projection"), "blueprint missing live disclosure projection contract");
assert(BLUEPRINT_SOURCE.includes("LiteratureAdapter"), "blueprint missing W2-6 adapter contract");
assert(BLUEPRINT_SOURCE.includes("spawn_requests"), "blueprint missing D4 governed fan-out contract");
assert(BLUEPRINT_SOURCE.includes("transformation_catalog.py"), "blueprint missing X0/X1 transformation contract");

function loadPlaywright() {
  const configured = process.env.MATHARC_PLAYWRIGHT_MODULE;
  if (configured) return require(configured);
  try {
    return require("playwright");
  } catch (_) {
    try {
      const npmRoot = execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim();
      return require(join(npmRoot, "playwright"));
    } catch (error) {
      fail(
        "Playwright is required. Install it locally, expose it through NODE_PATH, or set "
          + "MATHARC_PLAYWRIGHT_MODULE to a Playwright module path. " + String(error.message),
      );
    }
  }
}

const PYTHON = process.env.PYTHON || "python3";

const WORKSPACE_SERVER_PROGRAM = String.raw`
import json
import sys
import subprocess
from pathlib import Path

from matharc.v02.console_export import ConsoleLocalProjectionConfig
from matharc.v02.difficulty_ledger import DifficultyLedger, DifficultyOutcome, DifficultyPrediction, OrdinalLevel, DIFFICULTY_DIMENSIONS
from matharc.v02.falsification import (
    KillTestKind, KillTestSpec, RouteEvaluationOutcome, RouteEvaluationRecord,
    attach_kill_test_spec, record_route_evaluation,
)
from matharc.v02.review import (
    ReviewerProfile, ReviewerRoster, nominate_for_review, set_reviewer_roster,
)
from matharc.v02.problem_gates import (
    CandidateProblem, GATE_IDS, GateEvidence, GateVerdict, ProblemGateStore,
    ProblemStatementVersion, ResultGraph,
)
from matharc.v02.topic_portfolio import (
    CriterionVerdict, TOPIC_CRITERIA, TopicCandidate, TopicCriterion,
    TopicPortfolio, TopicPortfolioStore, TopicState,
)
from matharc.operations import (
    Account, CreditDirection, CreditEntry,
    SeatAllocation, UpstreamConfiguration,
)
from matharc.v02.operations_ledger import WorkspaceBoundOperationsLedger
from matharc.v02.schema import (
    ClaimRecord, ClaimStatus, ResearchRoute, RouteStatus, TheoremContract,
    ToolCallRecord, ToolStatus,
)
from matharc.v02.trace import ResearchTrace, save_trace
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workspace_server import make_server

root = Path(sys.argv[1])
dashboard = Path(sys.argv[2])
workspace_root = root / "workspace"
review_trace_path = root / "review-trace.json"
review_token = "browser-review-token"
reviewer = ReviewerProfile(
    reviewer_id="reviewer-A", name="A", affiliation="", independence_group="group-A"
)

write_full_workspace_bundle(workspace_root)
fake_claude = root / "fake-claude.py"
fake_claude.write_text("""#!/usr/bin/env python3
import json
print(json.dumps({"result": {"status": "blocked", "public_reasoning": {
    "objective": "browser fixture", "premises": ["CLI invocation"],
    "proposed_move": "record a bounded campaign round", "observation": "fixture",
    "falsification": "replay the emitted event", "decision": "blocked"
}, "claim_boundary": "browser gate fixture"}}))
""", encoding="utf-8")
fake_claude.chmod(0o755)
completed = subprocess.run(
    [sys.executable, "-m", "matharc.v02.cli", "run", "--workspace-root", str(workspace_root),
     "--role", "prover", "--rounds", "1", "--max-rounds-without-gain", "1",
     "--wall-seconds-budget", "1", "--claude-executable", str(fake_claude)],
    cwd=root, capture_output=True, text=True, check=False,
)
if completed.returncode != 0:
    raise RuntimeError(f"CLI campaign fixture failed: {completed.stderr or completed.stdout}")
if "campaign_artifact_id" not in json.loads(completed.stdout):
    raise RuntimeError("CLI campaign fixture did not emit a campaign artifact")
workspace = ResearchWorkspace.load(workspace_root)

# M3 fixture: every local-completion view receives a real, independently
# persisted projection.  The browser gate must prove these records render;
# not_configured is covered by the unit boundary tests instead.
topic_root = root / "topic-portfolio"
criteria = tuple(
    TopicCriterion(item, CriterionVerdict.DECLARED, (f"E-{index}",), "fixture evidence")
    for index, item in enumerate(TOPIC_CRITERIA, start=1)
)
TopicPortfolioStore(str(topic_root)).create(
    TopicPortfolio(
        "PORT-BROWSER", 3,
        (TopicCandidate("TOPIC-1", "Fixture topic", TopicState.ACTIVE, 1, criteria, ("OBS-1",)),),
    )
)

problem_root = root / "candidate-problems"
statement = ProblemStatementVersion("P-BROWSER", 1, "Fixture candidate problem")
gates = tuple(
    GateEvidence(item, GateVerdict.PASSED, f"G-{index}", "2026-01-01T00:00:00Z")
    for index, item in enumerate(GATE_IDS, start=1)
)
candidate = CandidateProblem("P-BROWSER", statement.statement_version_id, gates)
ProblemGateStore(str(problem_root)).replace(
    (statement,), (candidate,), ResultGraph((statement.statement_version_id,), ())
)

difficulty_root = root / "difficulty-ledger"
difficulty = DifficultyLedger(str(difficulty_root))
dimensions = tuple((item, OrdinalLevel.MEDIUM) for item in DIFFICULTY_DIMENSIONS)
difficulty.add_prediction(DifficultyPrediction("D-BROWSER", "P-BROWSER", dimensions, ("E-1",), "2026-01-01T00:00:00Z"))
difficulty.record_outcome(DifficultyOutcome("O-BROWSER", "D-BROWSER", dimensions, "2026-01-01T00:00:01Z"))

operations_root = root / "operations-domain"
operations = WorkspaceBoundOperationsLedger(
    operations_root,
    {
        "run_id": workspace.trace.run_id,
        "state_digest_sha256": workspace.state_digest(),
        "event_head_hash": workspace.events.head_hash,
        "workspace_root": str(workspace_root.resolve()),
    },
)
operations.create_account(Account("A-BROWSER", "Fixture account"))
operations.record_credit(CreditEntry("C-BROWSER", "A-BROWSER", CreditDirection.GRANT, 7, "fixture grant"))
operations.allocate_seat(SeatAllocation("S-BROWSER", "A-BROWSER", 2))
operations.configure_upstream(UpstreamConfiguration("U-BROWSER", "Fixture provider", {"provider_kind": "fixture", "region": "local"}))

trace = ResearchTrace("BROWSER-REVIEW", TheoremContract("K", "p", ("C",), "s"))
trace.add_claim(
    ClaimRecord("C", "n + 1 = 1 + n", "all integers n", status=ClaimStatus.CANDIDATE, owner="p1")
)
trace.add_route(
    ResearchRoute("R", "direct", "commute", ("m",), "kt", status=RouteStatus.ACTIVE,
                  claim_ids=("C",), created_by="route-proposer")
)
spec = KillTestSpec(
    kind=KillTestKind.ENUMERATION,
    generator_spec={"range": [0, 10]}, discriminator_spec={"check": "commutativity"},
    tested_scope="n in [0, 10)",
)
attach_kill_test_spec(trace, "R", spec)
trace.add_tool_call(
    ToolCallRecord(
        call_id="TC-1", tool="enumeration", purpose="check", status=ToolStatus.PASS,
        input_digest_sha256="a" * 64, output_digest_sha256="b" * 64,
        linked_claim_ids=("C",), independence_group="exact:1",
        replay_command="python -m matharc.v02 replay",
        started_at="2026-01-01T00:00:00Z", ended_at="2026-01-01T00:00:01Z",
    )
)
record_route_evaluation(
    trace,
    RouteEvaluationRecord(
        evaluation_id="EVAL-1", route_id="R", route_revision=0, claim_id="C",
        claim_revision=0, kill_test_spec_digest=spec.digest_sha256, tool_call_id="TC-1",
        outcome=RouteEvaluationOutcome.PASS_BOUNDED, tested_scope=spec.tested_scope,
        verifier_group="exact:1", replay_command="python -m matharc.v02 replay",
    ),
)
nominate_for_review(trace, "C")
set_reviewer_roster(trace, ReviewerRoster(roster_version="roster-1", reviewers=(reviewer,)))
save_trace(trace, review_trace_path)

server = make_server(
    workspace_root, host="127.0.0.1", port=0, dashboard_path=dashboard,
    sse_poll_seconds=0.02, sse_lifetime_seconds=0.35,
    local_projection_config=ConsoleLocalProjectionConfig(
        workspace_index_root=root,
        topic_portfolio_root=topic_root,
        problem_gate_root=problem_root,
        difficulty_ledger_root=difficulty_root,
        operations_domain_root=operations_root,
        novelty_audit_path=Path.cwd() / "agents-results/2026-08-31/problem-intelligence-plane/evidence/s2-fixtures/q6-candidate-audit.json",
        route_regression_path=Path.cwd() / "agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json",
        dogfood_archive_path=Path.cwd() / "agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures/three-real-archives.json",
    ),
    review_trace_path=review_trace_path, review_write_token=review_token,
)
print(json.dumps({
    "origin": f"http://127.0.0.1:{server.server_address[1]}",
    "workspace_root": str(workspace_root), "review_trace_path": str(review_trace_path),
    "review_token": review_token, "reviewer_id": reviewer.reviewer_id,
    "reviewer_profile_digest": reviewer.digest_sha256,
    "cli_executable": str(fake_claude),
}), flush=True)
server.serve_forever(poll_interval=0.02)
`;

const RECORD_CAMPAIGN_PROGRAM = String.raw`
import json
import sys
import subprocess
from pathlib import Path

from matharc.v02.workspace import ResearchWorkspace

completed = subprocess.run(
    [sys.executable, "-m", "matharc.v02.cli", "run", "--workspace-root", sys.argv[1],
     "--role", "prover", "--rounds", "1", "--max-rounds-without-gain", "1",
     "--wall-seconds-budget", "1", "--claude-executable", sys.argv[2]],
    cwd=Path(sys.argv[1]).parents[1], capture_output=True, text=True, check=False,
)
if completed.returncode != 0:
    raise RuntimeError(f"CLI campaign mutation failed: {completed.stderr or completed.stdout}")
if "campaign_artifact_id" not in json.loads(completed.stdout):
    raise RuntimeError("CLI campaign mutation did not emit a campaign artifact")
workspace = ResearchWorkspace.load(Path(sys.argv[1]))
print(json.dumps({"tail": workspace.events.events[-1].sequence}))
`;

const REVIEW_STATE_PROGRAM = String.raw`
import json
import sys
from pathlib import Path

from matharc.v02.review import reviews_for_claim
from matharc.v02.trace import load_trace

trace = load_trace(Path(sys.argv[1]))
reviews = reviews_for_claim(trace, "C")
print(json.dumps({
    "review_count": len(reviews),
    "active_review_count": sum(item.lifecycle_status.value == "ACTIVE" for item in reviews),
    "evidence_ids": sorted(trace.evidence),
}))
`;

function pythonEnvironment() {
  return { ...process.env, PYTHONPATH: [ROOT, process.env.PYTHONPATH].filter(Boolean).join(":") };
}

function runPython(program, args, label) {
  const completed = spawnSync(PYTHON, ["-c", program, ...args], {
    cwd: ROOT,
    encoding: "utf8",
    env: pythonEnvironment(),
  });
  if (completed.status !== 0) fail(`${label}: ${completed.stderr || completed.stdout}`);
  try {
    return JSON.parse(completed.stdout);
  } catch (error) {
    fail(`${label} emitted invalid JSON: ${completed.stdout || error.message}`);
  }
}

function wait(milliseconds) {
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function waitFor(predicate, message, timeout = 8000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await predicate()) return;
    await wait(25);
  }
  fail(message);
}

async function startServer() {
  const directory = mkdtempSync(join(tmpdir(), "matharc-console-browser-"));
  const child = spawn(PYTHON, ["-u", "-c", WORKSPACE_SERVER_PROGRAM, directory, PAGE_PATH], {
    cwd: ROOT,
    env: pythonEnvironment(),
    stdio: ["ignore", "pipe", "pipe"],
  });
  let stderr = "";
  let buffer = "";
  let settled = false;
  let resolveReady;
  let rejectReady;
  const ready = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
  child.stderr.setEncoding("utf8");
  child.stderr.on("data", chunk => { stderr += chunk; });
  child.stdout.setEncoding("utf8");
  child.stdout.on("data", chunk => {
    buffer += chunk;
    let newline;
    while ((newline = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (!line || settled) continue;
      try {
        settled = true;
        resolveReady(JSON.parse(line));
      } catch (error) {
        settled = true;
        rejectReady(new Error(`workspace fixture emitted invalid readiness JSON: ${line}; ${error.message}`));
      }
    }
  });
  child.once("error", error => {
    if (!settled) {
      settled = true;
      rejectReady(error);
    }
  });
  child.once("exit", (code, signal) => {
    if (!settled) {
      settled = true;
      rejectReady(new Error(`workspace fixture stopped before readiness (code=${code}, signal=${signal}): ${stderr}`));
    }
  });
  const details = await ready;
  return {
    ...details,
    campaignMutation() {
      return runPython(RECORD_CAMPAIGN_PROGRAM, [details.workspace_root, details.cli_executable], "could not record a live campaign result");
    },
    reviewState() {
      return runPython(REVIEW_STATE_PROGRAM, [details.review_trace_path], "could not read review fixture state");
    },
    diagnostics() { return stderr; },
    async close() {
      if (child.exitCode === null && !child.killed) child.kill("SIGTERM");
      await waitFor(
        () => child.exitCode !== null || child.signalCode !== null,
        "workspace fixture did not stop",
        5000,
      );
      rmSync(directory, { recursive: true, force: true });
    },
  };
}

async function dispatch(page, action, data = {}) {
  await page.evaluate(({ action, data }) => {
    const trigger = document.createElement("button");
    trigger.dataset.act = action;
    for (const [key, value] of Object.entries(data)) trigger.dataset[key] = String(value);
    document.body.appendChild(trigger);
    trigger.click();
    trigger.remove();
  }, { action, data });
  await page.waitForTimeout(0);
}

async function selectCampaign(page, id) {
  await dispatch(page, "camp", { id });
}

async function renderCase(page, campaignId, testCase) {
  await selectCampaign(page, campaignId);
  await dispatch(page, "go", { v: testCase.view });
  if (testCase.action) await dispatch(page, testCase.action[0], testCase.action[1]);
  const text = await page.locator("body").innerText();
  assert(!/(?:\bundefined\b|\bNaN\b|\[object Object\])/.test(text), `${campaignId}/${testCase.name} rendered a placeholder token`);
  assert(await page.locator("#nowtask, #page").count() > 0, `${campaignId}/${testCase.name} did not render a page surface`);
}

async function measureBalance(page, label, width) {
  const imbalances = await page.evaluate(() => {
    const issue = [];
    for (const grid of document.querySelectorAll(".grid2")) {
      const children = [...grid.children].filter(child => getComputedStyle(child).display !== "none");
      if (children.length !== 2) continue;
      const saved = children.map(child => ({
        height: child.style.height, maxHeight: child.style.maxHeight, overflow: child.style.overflow,
      }));
      const alignItems = grid.style.alignItems;
      grid.style.alignItems = "start";
      children.forEach(child => { child.style.height = "auto"; child.style.maxHeight = "none"; child.style.overflow = "visible"; });
      const heights = children.map(child => Math.round(child.getBoundingClientRect().height));
      grid.style.alignItems = alignItems;
      children.forEach((child, index) => Object.assign(child.style, saved[index]));
      const high = Math.max(...heights), low = Math.min(...heights);
      if (high === 0) continue;
      const difference = high - low, ratio = low / high;
      if (difference > 140 || ratio < 0.62) issue.push({ heights, difference, ratio: Number(ratio.toFixed(3)), text: grid.innerText.slice(0, 90) });
    }
    return issue;
  });
  assert(imbalances.length === 0, `${label} at ${width}px has unbalanced two-column content: ${JSON.stringify(imbalances[0])}`);
}

async function scanChineseEnglish(page, label) {
  const hits = await page.evaluate(() => {
    const finder = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || parent.closest(".mono, .hash, script, style")) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const bad = [];
    while (finder.nextNode()) {
      const text = finder.currentNode.textContent || "";
      const match = text.match(/[\u3400-\u9fff][A-Za-z_][A-Za-z0-9_]*/);
      if (match) bad.push(match[0]);
    }
    return bad;
  });
  assert(hits.length === 0, `${label} contains Chinese text adjacent to a bare English identifier: ${hits[0]}`);
}

async function testAccordions(page) {
  const views = ["source", "campaign", "exploration", "tools", "reasoning", "proofchain"];
  for (const view of views) {
    await renderCase(page, "c7", { name: view, view });
    const targets = await page.locator(".cev[data-act]").evaluateAll(nodes => nodes.map(node => ({
      action: node.dataset.act,
      id: node.dataset.id,
      i: node.dataset.i,
    })).filter(node => node.action));
    for (const target of targets) {
      const data = target.id !== undefined ? { id: target.id } : { i: target.i };
      const selector = target.id !== undefined
        ? `.cev[data-act="${target.action}"][data-id="${target.id}"]`
        : `.cev[data-act="${target.action}"][data-i="${target.i}"]`;
      if (await page.locator(selector).evaluate(node => node.classList.contains("open"))) {
        await dispatch(page, target.action, data);
      }
      assert(!(await page.locator(selector).evaluate(node => node.classList.contains("open"))), `${view}/${target.action} did not normalize to closed`);
      await dispatch(page, target.action, data);
      assert(await page.locator(selector).evaluate(node => node.classList.contains("open")), `${view}/${target.action} did not expand in place`);
      await dispatch(page, target.action, data);
      assert(!(await page.locator(selector).evaluate(node => node.classList.contains("open"))), `${view}/${target.action} did not close in place`);
    }
  }
}

async function testKeyboardControls(page) {
  await renderCase(page, "c7", { name: "source-keyboard", view: "source" });
  const selector = '.cev[data-act="obs"][data-id="o1"]';
  const normalizeClosed = async () => {
    const target = page.locator(selector);
    await target.waitFor({ state: "visible" });
    if (await target.evaluate(node => node.classList.contains("open"))) {
      await dispatch(page, "obs", { id: "o1" });
    }
    assert(!(await page.locator(selector).evaluate(node => node.classList.contains("open"))), "keyboard fixture did not normalize closed");
  };
  await normalizeClosed();

  const enterTarget = page.locator(selector);
  await enterTarget.focus();
  assert(await enterTarget.evaluate(node => document.activeElement === node), "Enter target did not receive focus");
  await page.keyboard.press("Enter");
  await waitFor(
    () => page.locator(selector).evaluate(node => node.classList.contains("open")),
    "Enter did not activate the tabindex disclosure control",
  );

  const spaceTarget = page.locator(selector);
  await spaceTarget.focus();
  assert(await spaceTarget.evaluate(node => document.activeElement === node), "Space target did not receive focus");
  await page.keyboard.press("Space");
  await waitFor(
    async () => !(await page.locator(selector).evaluate(node => node.classList.contains("open"))),
    "Space did not activate the tabindex disclosure control",
  );
}

async function testMobileViewports(browser, server) {
  for (const viewport of MOBILE_VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      isMobile: true,
      hasTouch: true,
      deviceScaleFactor: 2,
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.stack || error.message));
    try {
      await page.goto(`${server.origin}/`, { waitUntil: "domcontentloaded" });
      await page.locator("#console-provenance").waitFor({ state: "attached" });
      const fellBackToDemo = await page.evaluate(() => window.MathArcConsole.loadExport("/missing-console.json"));
      assert(!fellBackToDemo, `${viewport.name} did not enter its declared demo-data baseline`);
      for (const campaignId of CAMPAIGNS) {
        for (const testCase of VIEW_CASES) {
          await renderCase(page, campaignId, testCase);
          await measureBalance(page, `${viewport.name}/${campaignId}/${testCase.name}`, viewport.width);
          await scanChineseEnglish(page, `${viewport.name}/${campaignId}/${testCase.name}`);
        }
      }
      await testKeyboardControls(page);
      assert(pageErrors.length === 0, `${viewport.name} page errors: ${pageErrors.join("\n")}`);
    } finally {
      await context.close();
    }
  }
}

async function testStartFlow(page) {
  await renderCase(page, "c7", { name: "portfolio", view: "portfolio" });
  await dispatch(page, "pick", { id: "full" });
  await dispatch(page, "go", { v: "portfolio" });
  assert(await page.locator('button[disabled]').filter({ hasText: "选择缺口并开始攻克" }).count() === 1, "a nine-gate failure did not leave exactly one disabled start button");
  await dispatch(page, "pick", { id: "resid" });
  await dispatch(page, "go", { v: "frontier" });
  await dispatch(page, "fnode", { id: "n7" });
  assert(await page.locator('[data-act="compile"]').count() === 1, "the residual-gap table did not expose exactly one compilable start action");
  await dispatch(page, "compile");
  assert((await page.locator("#nowtask").innerText()).includes("攻克进程"), "compiling a residual gap did not enter the campaign flow");
}

async function tamperSnapshot(page, mode) {
  await renderCase(page, "c7", { name: "proofchain", view: "proofchain" });
  await dispatch(page, "tamper", { m: mode });
  return page.evaluate(() => ({
    title: document.querySelector("#nowtask")?.innerText || "",
    badRows: document.querySelectorAll(".cev.bad").length,
    body: document.body.innerText,
  }));
}

async function testTampers(page) {
  const original = await tamperSnapshot(page, "off");
  assert(original.body.includes("两道防线都通过"), "original event ledger did not verify");
  const edit = await tamperSnapshot(page, "edit");
  assert(edit.body.includes("逐条复算报出 1 项错误") && edit.badRows === 1, "payload edit did not produce the one-error hash signature");
  const deletion = await tamperSnapshot(page, "delete");
  const swap = await tamperSnapshot(page, "swap");
  const insert = await tamperSnapshot(page, "insert");
  const rewrite = await tamperSnapshot(page, "rewrite");
  for (const [mode, snapshot] of Object.entries({ delete: deletion, swap, insert })) {
    assert(snapshot.body.includes("第一道防线拦下") && snapshot.badRows > 0, `${mode} was not caught by per-event validation`);
  }
  const signatures = new Set([deletion.badRows, swap.badRows, insert.badRows]);
  assert(signatures.size === 3, `delete/swap/insert must have distinct tamper signatures, got ${[...signatures].join(", ")}`);
  assert(rewrite.body.includes("第二道防线拦下") && rewrite.body.includes("逐条复算全部通过"), "full-chain rewrite did not require the external-head check");
}

async function testDataBoundaryAndProvenance(page, server, exportPayload) {
  await page.evaluate(() => window.MathArcConsole.loadExport("/missing-console.json"));
  for (const view of LIVE_VIEWS) {
    await renderCase(page, "c7", { name: `${view}-fallback`, view });
    assert(await page.locator("#view-data-boundary").evaluate(node => node.dataset.source === "demo"), `${view} fallback lost its demo label`);
  }

  const loaded = await page.evaluate(() => window.MathArcConsole.loadExport("/api/console"));
  assert(loaded, "real console export was rejected by the browser bridge");
  const expected = {
    source: exportPayload.source_topic.source_claims.length,
    dag: exportPayload.workspace.trace.claims.length,
    proofchain: exportPayload.workspace.events.events.length,
    tools: exportPayload.workspace.trace.tool_calls.length,
    reasoning: exportPayload.workspace.trace.public_reasoning.length,
    admin_roles: Object.keys(exportPayload.role_policy.grants).length,
    campaign: exportPayload.local_console.workspace_index.workspaces.length,
    routes: exportPayload.routes.routes.length,
    disclosure: exportPayload.disclosure.records.state.length,
    novelty: exportPayload.novelty.audit.route_results.length,
  };
  for (const [view, count] of Object.entries(expected)) {
    await renderCase(page, "c7", { name: `${view}-live`, view });
    const text = await page.locator("body").innerText();
    assert(await page.locator("#view-data-boundary").evaluate(node => node.dataset.source === "live"), `${view} retained a demo label after a declared live export`);
    assert(text.includes(String(count)), `${view} has no browser-visible numeric value derived from its real JSON count ${count}`);
    if (view === "routes") assert(!text.includes("分层枚举路线"), "routes live renderer leaked its demonstration route name");
    if (view === "disclosure") assert(!text.includes("六外部元素桥接构造"), "disclosure live renderer leaked its demonstration result name");
    if (view === "novelty") {
      assert(!text.includes("检索协议 版本 2"), "novelty live renderer leaked SEARCH_PROTO demonstration constants");
      assert(text.includes(exportPayload.novelty.audit.audit_id), "novelty live renderer omitted the persisted audit id");
    }
  }
  assert(exportPayload.local_console.route_regression.state === "live", "R1 four-route projection was not exported");
  assert(exportPayload.local_console.route_regression.route_order.join(",") === "FORWARD_CITATION,ALIAS_AND_EQUIVALENCE,STRUCTURAL_SEMANTIC,REVIEW_AND_EXPERT_LEAD", "R1 route order drifted");
  assert(exportPayload.local_console.route_regression.cases.length === 3, "R1 route projection omitted a fixed case");
  assert(exportPayload.local_console.dogfood_archives.state === "live", "T2 dogfood archive projection was not exported");
  assert(exportPayload.local_console.dogfood_archives.cases.length === 3, "T2 archive projection omitted a fixed case");
  for (const view of ["acct_usage"]) {
    await renderCase(page, "c7", { name: `${view}-unwired`, view });
    const boundary = await page.locator("#view-data-boundary").getAttribute("data-source");
    assert(boundary === "demo" || (FAIL_CLOSED_M2_VIEWS.has(view) && boundary === "unavailable"), `${view} is not declared live but its demo label disappeared`);
  }
}

async function testM3LocalProjections(page, exportPayload) {
  const local = exportPayload.local_console;
  assert(local.workspace_index.state === "live", "M3 workspace index projection was not live");
  assert(local.topic_portfolio.state === "live", "M3 topic portfolio projection was not live");
  assert(local.candidate_problems.state === "live", "M3 candidate problem projection was not live");
  assert(local.difficulty_ledger.state === "live", "M3 difficulty projection was not live");
  assert(local.operations.state === "live", "M3 operations projection was not live");
  const cases = [
    ["campaign", local.workspace_index.workspaces.length],
    ["topics", local.topic_portfolio.candidates.length],
    ["portfolio", local.candidate_problems.candidates.length],
    ["dossier", local.candidate_problems.statements.length],
    ["frontier", local.candidate_problems.graph.nodes.length],
    ["difficulty", local.difficulty_ledger.predictions.length],
    ["admin_users", local.operations.accounts.length],
    ["admin_upstream", local.operations.upstreams.length],
  ];
  for (const [view, count] of cases) {
    await renderCase(page, "c7", { name: `m3-${view}`, view });
    const text = await page.locator("body").innerText();
    assert(
      await page.locator("#view-data-boundary").evaluate(node => node.dataset.source === "live"),
      `M3 ${view} lost its live data-boundary marker`,
    );
    assert(text.includes(String(count)), `M3 ${view} omitted browser-visible projection count ${count}`);
  }
}

async function testM1SseAndReconnect(page, server, eventCursors) {
  const initial = await (await fetch(`${server.origin}/api/console`)).json();
  const initialTail = initial.workspace.events.events.at(-1).sequence;
  await renderCase(page, "c7", { name: "proofchain-before-sse", view: "proofchain" });
  const beforeSse = await page.locator("body").innerText();
  // The 52 x 2 x 6 visual sweep can outlive the short-lived fixture stream.
  // Re-establish the real stream at the M1 boundary so this assertion does
  // not depend on the page-load connection surviving the sweep.
  await page.evaluate(() => window.MathArcConsole.connectEvents("/events"));
  await waitFor(
    () => eventCursors.includes(initialTail),
    `M1 did not connect to /events with initial cursor ${initialTail}`,
  );
  const requestsBeforeMutation = eventCursors.length;
  const refreshed = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === "/api/console" && response.request().method() === "GET";
  });
  const mutation = server.campaignMutation();
  assert(mutation.tail > initialTail, "M1 workspace mutation did not append a new event");
  const refreshResponse = await refreshed;
  assert(refreshResponse.status() === 200, "M1 event refresh did not receive a console export");
  const refreshedPayload = await refreshResponse.json();
  assert(
    refreshedPayload.workspace.events.events.at(-1).sequence === mutation.tail,
    "M1 event refresh did not load the workspace state containing the emitted event",
  );
  const refreshedDigest = String(refreshedPayload.provenance.state_digest_sha256).slice(0, 12);
  await waitFor(
    async () => {
      const body = await page.locator("body").innerText();
      const provenance = await page.locator("#console-provenance").innerText();
      return body !== beforeSse && body.includes(String(mutation.tail)) && provenance.includes(refreshedDigest);
    },
    `M1 SSE refresh did not render the newly emitted event ${mutation.tail} in the page`,
  );
  await renderCase(page, "c7", { name: "campaign-after-sse", view: "campaign" });
  assert((await page.locator("#nowtask").innerText()).includes("真实报告"), "M1 event refresh did not render the live campaign report");
  await waitFor(
    () => eventCursors.slice(requestsBeforeMutation).includes(mutation.tail),
    `M1 reconnect did not continue from event cursor ${mutation.tail}`,
  );
  return `emitted event ${mutation.tail}, refreshed /api/console, and reconnected with after=${mutation.tail}`;
}

async function fillReviewForm(page, server, reviewId, verdict) {
  await page.locator("#review-id").fill(reviewId);
  await page.locator("#reviewer-id").fill(server.reviewer_id);
  await page.locator("#reviewer-roster-version").fill("roster-1");
  await page.locator("#reviewer-profile-digest").fill(server.reviewer_profile_digest);
  await page.locator("#review-policy-version").fill("policy-1");
  await page.locator("#review-decision").selectOption("APPROVE");
  await page.locator("#review-statement-correspondence").fill("matches");
  const verdicts = page.locator("[data-review-verdict]");
  const count = await verdicts.count();
  assert(count > 0, "M2 real review bundle rendered no obligation verdict controls");
  for (let index = 0; index < count; index += 1) await verdicts.nth(index).selectOption(verdict);
  await page.locator("#review-token").fill(server.review_token);
}

async function testM2ReviewWorkflow(page, server) {
  await dispatch(page, "go", { v: "admin_queue" });
  const bundleButton = page.getByRole("button", { name: "打开送审包", exact: true });
  await bundleButton.waitFor({ state: "visible" });
  assert(
    await page.locator("#view-data-boundary").evaluate(node => node.dataset.source === "live"),
    "M2 review queue was not rendered from the same-origin review service",
  );
  const bundleResponse = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === "/api/review-bundle/C" && response.request().method() === "GET";
  });
  await bundleButton.click();
  const response = await bundleResponse;
  assert(response.status() === 200, "M2 review bundle endpoint did not return the rendered claim bundle");
  await page.locator("#review-id").waitFor({ state: "visible" });
  assert((await page.locator("body").innerText()).includes("n + 1 = 1 + n"), "M2 rendered review form omitted the real bundle statement");

  await fillReviewForm(page, server, "REV-BROWSER-REJECT", "GAP");
  const rejectedPost = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === "/api/review" && response.request().method() === "POST";
  });
  await page.getByRole("button", { name: "提交评审", exact: true }).click();
  const rejectedResponse = await rejectedPost;
  assert(rejectedResponse.status() === 400, "M2 APPROVE with a non-OK obligation was not rejected by the domain contract");
  const rejectedPayload = await rejectedResponse.json();
  assert(rejectedPayload.error === "malformed_review", "M2 rejected submission did not expose the domain validation response");
  await page.getByText("评审未被接受。", { exact: true }).waitFor({ state: "visible" });
  assert(await page.locator("#review-token").inputValue() === "", "M2 rejected submission retained the review token in the form");
  const rejectedState = server.reviewState();
  assert(rejectedState.review_count === 0 && rejectedState.evidence_ids.length === 0, "M2 rejected submission mutated the review trace");

  await fillReviewForm(page, server, "REV-BROWSER-APPROVE", "OK");
  const approvedPost = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === "/api/review" && response.request().method() === "POST";
  });
  await page.getByRole("button", { name: "提交评审", exact: true }).click();
  const approvedResponse = await approvedPost;
  assert(approvedResponse.status() === 200, "M2 valid rendered review submission was not accepted");
  const approvedPayload = await approvedResponse.json();
  assert(approvedPayload.submitted === true && approvedPayload.evidence_id === "EV-REVIEW-REV-BROWSER-APPROVE", "M2 success response did not bind the review evidence");
  await page.getByText("评审已提交。", { exact: true }).waitFor({ state: "visible" });
  await waitFor(async () => (await page.locator("body").innerText()).includes("已有 1 份生效评审"), "M2 queue did not refresh after a valid review submission");
  const approvedState = server.reviewState();
  assert(
    approvedState.review_count === 1
      && approvedState.active_review_count === 1
      && approvedState.evidence_ids.includes("EV-REVIEW-REV-BROWSER-APPROVE"),
    "M2 valid submission did not persist the active review and evidence",
  );
  return "exercised real queue, bundle, rendered rejection, token clearing, and persisted approval";
}

async function main() {
  assert(VIEW_CASES.length === 52, `case inventory must remain 52 views, got ${VIEW_CASES.length}`);
  const declaredViews = new Set([...PAGE_SOURCE.matchAll(/\bV\.([A-Za-z_][A-Za-z0-9_]*)\s*=/g)].map(match => match[1]));
  const coveredViews = new Set(VIEW_CASES.map(testCase => testCase.view));
  for (const view of declaredViews) assert(coveredViews.has(view), `declared view ${view} has no browser case`);

  const playwright = loadPlaywright();
  const server = await startServer();
  let exportResponse;
  try {
    exportResponse = await fetch(`${server.origin}/api/console`);
  } catch (error) {
    fail(`initial console export fetch failed: ${error.message}; fixture stderr: ${server.diagnostics()}`);
  }
  const exportPayload = await exportResponse.json();
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: WIDTHS[0], height: 1080 } });
  const pageErrors = [];
  const eventCursors = [];
  page.on("pageerror", error => pageErrors.push(error.stack || error.message));
  page.on("request", request => {
    const url = new URL(request.url());
    if (url.pathname !== "/events") return;
    const cursor = Number(url.searchParams.get("after"));
    if (Number.isInteger(cursor)) eventCursors.push(cursor);
  });
  try {
    await page.goto(`${server.origin}/`, { waitUntil: "domcontentloaded" });
    await page.locator("#console-provenance").waitFor({ state: "attached" });
    const fellBackToDemo = await page.evaluate(() => window.MathArcConsole.loadExport("/missing-console.json"));
    assert(!fellBackToDemo, "prototype regression cases did not enter their declared demo-data baseline");
    for (const width of WIDTHS) {
      await page.setViewportSize({ width, height: 1080 });
      for (const campaignId of CAMPAIGNS) {
        for (const testCase of VIEW_CASES) {
          await renderCase(page, campaignId, testCase);
          await measureBalance(page, `${campaignId}/${testCase.name}`, width);
          await scanChineseEnglish(page, `${campaignId}/${testCase.name}`);
        }
      }
    }
    await testAccordions(page);
    await testStartFlow(page);
    await testTampers(page);
    await testDataBoundaryAndProvenance(page, server, exportPayload);
    await testM3LocalProjections(page, exportPayload);
    const m1 = await testM1SseAndReconnect(page, server, eventCursors);
    const m2 = await testM2ReviewWorkflow(page, server);
    await testMobileViewports(browser, server);
    assert(pageErrors.length === 0, `page errors: ${pageErrors.join("\n")}`);
    console.log(`console browser gate passed: ${VIEW_CASES.length} cases x ${CAMPAIGNS.length} campaigns x ${WIDTHS.length} widths`);
    console.log(`mobile viewport checks passed: ${MOBILE_VIEWPORTS.map(viewport => `${viewport.name}=${viewport.width}x${viewport.height}`).join(", ")}`);
    console.log("keyboard checks passed: tabindex disclosures activated with Enter and Space");
    console.log(`M1 SSE workflow: ${m1}`);
    console.log(`M2 review workflow: ${m2}`);
  } finally {
    await browser.close();
    await server.close();
  }
}

main().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
