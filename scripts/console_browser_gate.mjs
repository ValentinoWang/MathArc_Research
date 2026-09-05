#!/usr/bin/env node
/*
 * Guard card: console-prototype-browser-regression
 * Failure class: a browser-rendered console view diverges from the declared
 * prototype contract (broken render, responsive imbalance, falsified ledger,
 * inaccessible in-place disclosure, lost data-origin boundary, broken access
 * lifecycle, secret retention, or component descendant-selector leakage that
 * collapses a nested text column). Scope: the local workspace/access fixture
 * and docs/prototypes/problem-intel-console.html; this does not prove deployed
 * or production behaviour. Runtime access captures are SHA-256-bound to a
 * manifest, and live console checks run with a server-issued Cookie session.
 * Repair: restore the declared browser/API boundary, keep secret values out of
 * persistence and evidence, and update this card only when the approved local
 * browser contract changes.
 */
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { execFileSync, spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative, resolve } from "node:path";

const require = createRequire(import.meta.url);
const ROOT = resolve(import.meta.dirname, "..");
const PAGE_PATH = resolve(ROOT, "docs/prototypes/problem-intel-console.html");
const PAGE_SOURCE = readFileSync(PAGE_PATH, "utf8");
const BLUEPRINT_PATH = resolve(ROOT, "docs/prototypes/console-dev-blueprint.html");
const BLUEPRINT_SOURCE = readFileSync(BLUEPRINT_PATH, "utf8");
// Evidence root: the default keeps the research-preview task's historical captures; a new task points
// MATHARC_GATE_EVIDENCE_DIR at its own agents-results directory so old evidence is never overwritten.
const EVIDENCE_DIR = resolve(ROOT, process.env.MATHARC_GATE_EVIDENCE_DIR || "agents-results/2026-09-03/research-preview-access");
const ACCESS_EVIDENCE_DIR = EVIDENCE_DIR;
const LANDING_EVIDENCE_DIR = EVIDENCE_DIR;
// Font mode is part of the evidence identity (view contract §9.13.4): "webfont-loaded" lets the page fetch
// fonts.googleapis.com; "fallback-local" blocks the font hosts so metrics come from installed system fonts.
// A machine without the CDN must declare fallback-local instead of letting the network decide.
const FONT_MODE = process.env.MATHARC_GATE_FONT_MODE || "webfont-loaded";
// The project copy lexicon is the single place for deliberate identifier exceptions; the runtime
// scan honours the same allowlist as scripts/check_ui_copy_quality.py so decisions are not duplicated.
const COPY_LEXICON = JSON.parse(readFileSync(resolve(ROOT, "docs/quality-gates/ui-copy-lexicon.json"), "utf8"));
const COPY_ALLOW_IDENTIFIERS = new Set(COPY_LEXICON.allow_identifiers || []);
const COPY_CONTAINER_SELECTOR = [".mono", ".hash", ".ev", ".seq", "code", "kbd", "pre", "samp", "var", "script", "style", "input", "textarea", "option",
  ...(COPY_LEXICON.identifier_container_classes || []).map(name => `.${name}`)].join(", ");
assert(FONT_MODE === "webfont-loaded" || FONT_MODE === "fallback-local", `unknown MATHARC_GATE_FONT_MODE ${FONT_MODE}`);
const FONT_HOSTS = /^https:\/\/fonts\.(?:googleapis|gstatic)\.com\//;
// Landing sections the scroll walk visits, in page order. Kept in one place so the summary line
// cannot drift from what was actually asserted.
const LANDING_SECTIONS = ["planes", "how", "case", "team", "nots"];
async function newGateContext(browser, options) {
  const context = await browser.newContext(options);
  if (FONT_MODE === "fallback-local") await context.route(FONT_HOSTS, route => route.abort());
  return context;
}
const ACCESS_COOKIE_NAME = "matharc_access_session";
const ACCESS_SCREENSHOT_VIEWPORTS = [
  { name: "desktop", width: 1240, height: 1080 },
  { name: "mobile", width: 390, height: 844 },
];
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
    "portfolio", "workbench", "dossier", "cert", "frontier", "radar", "source", "novelty", "difficulty", "dag", "disclosure",
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

from matharc.v02.access import InvitationAccessStore
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
access_root = root / "access-domain"
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

access_store = InvitationAccessStore(access_root, session_ttl_seconds=43200)
ui_invitation_email = "browser-access@example.edu"
ui_invitation = access_store.issue_invitation(
    email=ui_invitation_email,
    topic_scopes=("combinatorics", "formal-proof"),
)
gate_invitation_email = "browser-gate@example.edu"
gate_invitation = access_store.issue_invitation(
    email=gate_invitation_email,
    topic_scopes=("browser-regression",),
)

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
    access_store_root=access_root,
)
print(json.dumps({
    "origin": f"http://127.0.0.1:{server.server_address[1]}",
    "workspace_root": str(workspace_root), "review_trace_path": str(review_trace_path),
    "review_token": review_token, "reviewer_id": reviewer.reviewer_id,
    "reviewer_profile_digest": reviewer.digest_sha256,
    "cli_executable": str(fake_claude),
    "access_state_path": str(access_store.path),
    "ui_invitation_email": ui_invitation_email,
    "ui_invitation_code": ui_invitation.code,
    "gate_invitation_email": gate_invitation_email,
    "gate_invitation_code": gate_invitation.code,
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

function assertInvitationSecretsNotPersisted(server) {
  const state = readFileSync(server.access_state_path, "utf8");
  for (const code of [server.ui_invitation_code, server.gate_invitation_code]) {
    assert(!state.includes(code), "access state persisted a plaintext invitation code");
  }
}

async function settleVisualLayout(page) {
  await page.evaluate(async () => {
    await document.fonts.ready;
    await new Promise(resolveFrame => requestAnimationFrame(() => requestAnimationFrame(resolveFrame)));
  });
  // A capture is evidence of the settled page: wait until nothing in the viewport is still revealing
  // (bounded, so a stuck attribute fails the reveal assertions instead of hanging the capture).
  await waitFor(
    async () => await page.evaluate(() => [...document.querySelectorAll('[data-reveal]')]
      // an element whose top sits in the bottom 10% of the viewport may legitimately still be pending (the
      // observer margin excludes that band), so only elements clearly inside the viewport must have settled
      .filter(node => { const rect = node.getBoundingClientRect(); return rect.bottom > 0 && rect.top < window.innerHeight * 0.9; })
      .every(node => node.dataset.reveal === "in" && getComputedStyle(node).opacity === "1")),
    "in-viewport reveal did not settle before capture",
    3000,
  );
}

async function captureAccessScenario(page, scenario, basename, manifestEntries) {
  for (const viewport of ACCESS_SCREENSHOT_VIEWPORTS) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await settleVisualLayout(page);
    const filename = `${viewport.name}-${basename}.png`;
    const outputPath = join(ACCESS_EVIDENCE_DIR, filename);
    const capturedAt = new Date().toISOString();
    await page.screenshot({ path: outputPath, fullPage: false });
    const digest = createHash("sha256").update(readFileSync(outputPath)).digest("hex");
    manifestEntries.push({
      file: relative(ROOT, outputPath),
      sha256: digest,
      scenario,
      page_identity: {
        title: await page.title(),
        path: new URL(page.url()).pathname,
      },
      browser: "chromium",
      viewport: { width: viewport.width, height: viewport.height },
      font_mode: FONT_MODE,
      captured_at: capturedAt,
      review_result: "PASS",
    });
  }
}

async function openPublicRoot(page, origin) {
  const sessionResponse = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === "/api/access/session" && response.request().method() === "GET";
  });
  await page.goto(`${origin}/`, { waitUntil: "domcontentloaded" });
  const response = await sessionResponse;
  assert(response.status() === 401, "fresh public context unexpectedly restored an access session");
  await page.getByRole("button", { name: "登录", exact: true }).waitFor({ state: "visible" });
}

function assertExactKeys(value, expected, label) {
  const actual = Object.keys(value || {}).sort();
  const wanted = [...expected].sort();
  assert(JSON.stringify(actual) === JSON.stringify(wanted), `${label} fields drifted: ${actual.join(",")}`);
}

async function assertNoAccessCookie(context, origin, label) {
  const cookies = await context.cookies(origin);
  assert(!cookies.some(cookie => cookie.name === ACCESS_COOKIE_NAME), `${label} created or retained an access cookie`);
}

async function testAccessWorkflow(browser, server) {
  mkdirSync(ACCESS_EVIDENCE_DIR, { recursive: true });
  const manifestEntries = [];

  const anonymousContext = await newGateContext(browser, { viewport: { width: 1240, height: 1080 } });
  try {
    const response = await anonymousContext.request.get(`${server.origin}/api/console`);
    assert(response.status() === 401, "anonymous protected console request was not rejected");
    const payload = await response.json();
    assert(payload.error === "access_required", "anonymous protected response lost its access_required contract");
    await assertNoAccessCookie(anonymousContext, server.origin, "anonymous protected request");
  } finally {
    await anonymousContext.close();
  }

  const applicationContext = await newGateContext(browser, { viewport: { width: 1240, height: 1080 } });
  try {
    const page = await applicationContext.newPage();
    await openPublicRoot(page, server.origin);
    await page.getByRole("button", { name: "登录", exact: true }).click();
    await page.getByRole("button", { name: "没有邀请码？申请研究预览", exact: true }).click();
    await page.locator("#f-mail").fill("browser-applicant@example.edu");
    await page.locator("#f-institution").fill("Example Mathematics Institute");
    await page.locator("#f-research-role").fill("Research fellow");
    await page.locator("#f-research-direction").fill("Combinatorics and formal proof");
    await page.locator("#f-purpose").fill("Evaluate evidence-bound mathematical research workflows.");
    const submitted = page.waitForResponse(response => {
      const url = new URL(response.url());
      return url.pathname === "/api/access/applications" && response.request().method() === "POST";
    });
    await page.getByRole("button", { name: "提交申请", exact: true }).click();
    const response = await submitted;
    assert(response.status() === 202, "public application did not return 202");
    const payload = await response.json();
    assertExactKeys(payload, ["application"], "application response");
    assertExactKeys(payload.application, ["application_id", "email", "status", "submitted_at"], "public application");
    assert(payload.application.status === "PENDING", "public application was not left pending");
    await page.getByText(/申请已提交并进入待审核队列/).waitFor({ state: "visible" });
    await assertNoAccessCookie(applicationContext, server.origin, "pending application");
    await captureAccessScenario(page, "application pending", "application-pending", manifestEntries);
  } finally {
    await applicationContext.close();
  }

  const invalidContext = await newGateContext(browser, { viewport: { width: 1240, height: 1080 } });
  try {
    const page = await invalidContext.newPage();
    await openPublicRoot(page, server.origin);
    await page.getByRole("button", { name: "登录", exact: true }).click();
    await page.locator("#f-mail").fill(server.ui_invitation_email);
    await page.locator("#f-code").fill("invalid-browser-invitation");
    const rejected = page.waitForResponse(response => {
      const url = new URL(response.url());
      return url.pathname === "/api/access/redeem" && response.request().method() === "POST";
    });
    await page.getByRole("button", { name: "进入", exact: true }).click();
    const response = await rejected;
    assert(response.status() === 401, "invalid invitation was not rejected");
    const payload = await response.json();
    assert(payload.error === "invalid_credentials" && payload.message === "邮箱或邀请码无效。", "invalid invitation response was not generic");
    await page.getByText("邮箱或邀请码无效。", { exact: true }).waitFor({ state: "visible" });
    assert(await page.locator("#f-code").inputValue() === "", "invalid invitation secret remained in the form");
    await assertNoAccessCookie(invalidContext, server.origin, "invalid invitation");
    await captureAccessScenario(page, "invalid invitation rejected", "invalid-invite", manifestEntries);
  } finally {
    await invalidContext.close();
  }

  const invitationContext = await newGateContext(browser, { viewport: { width: 1240, height: 1080 } });
  let restoredPage;
  try {
    const page = await invitationContext.newPage();
    await openPublicRoot(page, server.origin);
    await page.getByRole("button", { name: "登录", exact: true }).click();
    await page.locator("#f-mail").fill(server.ui_invitation_email);
    await page.locator("#f-code").fill(server.ui_invitation_code);
    const redeemed = page.waitForResponse(response => {
      const url = new URL(response.url());
      return url.pathname === "/api/access/redeem" && response.request().method() === "POST";
    });
    await page.getByRole("button", { name: "进入", exact: true }).click();
    const response = await redeemed;
    assert(response.status() === 200, "valid invitation was not redeemed");
    const payload = await response.json();
    assert(payload.authenticated === true && payload.session.email === server.ui_invitation_email, "valid invitation returned the wrong session");
    const setCookie = await response.headerValue("set-cookie") || "";
    assert(/(?:^|;)\s*Path=\//i.test(setCookie), "session cookie lost Path=/");
    assert(/(?:^|;)\s*HttpOnly(?:;|$)/i.test(setCookie), "session cookie lost HttpOnly");
    assert(/(?:^|;)\s*SameSite=Strict(?:;|$)/i.test(setCookie), "session cookie lost SameSite=Strict");
    assert(/(?:^|;)\s*Max-Age=\d+(?:;|$)/i.test(setCookie), "session cookie lost bounded Max-Age");
    assert(!/(?:^|;)\s*Domain=/i.test(setCookie), "local session cookie unexpectedly declared Domain");
    assert(!/(?:^|;)\s*Secure(?:;|$)/i.test(setCookie), "local HTTP session cookie unexpectedly declared Secure");
    const cookies = await invitationContext.cookies(server.origin);
    const accessCookie = cookies.find(cookie => cookie.name === ACCESS_COOKIE_NAME);
    assert(accessCookie && accessCookie.httpOnly && accessCookie.sameSite === "Strict" && accessCookie.path === "/", "browser did not store the hardened session cookie");
    await page.getByText("邀请码已确认，已进入研究预览。", { exact: true }).waitFor({ state: "visible" });
    assert(await page.locator("#f-code").count() === 0, "redeemed invitation secret remained in the rendered DOM");
    assert(!(await page.locator("body").innerText()).includes(server.ui_invitation_code), "redeemed invitation secret became visible");
    const protectedResponse = await invitationContext.request.get(`${server.origin}/api/console`);
    assert(protectedResponse.status() === 200, "redeemed browser session did not authorize the console");

    restoredPage = await invitationContext.newPage();
    const sessionResponse = restoredPage.waitForResponse(candidate => {
      const url = new URL(candidate.url());
      return url.pathname === "/api/access/session" && candidate.request().method() === "GET";
    });
    await restoredPage.goto(`${server.origin}/`, { waitUntil: "domcontentloaded" });
    assert((await sessionResponse).status() === 200, "same-context page did not restore the Cookie session");
    await restoredPage.locator("#access-logout").waitFor({ state: "visible" });
    await waitFor(
      () => restoredPage.locator("#view-data-boundary").evaluate(node => node.dataset.source === "live"),
      "restored session did not render the protected live console",
    );
    await page.close();
    await captureAccessScenario(restoredPage, "Cookie session restored", "session-restored", manifestEntries);

    const replayContext = await newGateContext(browser, { viewport: { width: 1240, height: 1080 } });
    try {
      const replayPage = await replayContext.newPage();
      await openPublicRoot(replayPage, server.origin);
      await replayPage.getByRole("button", { name: "登录", exact: true }).click();
      await replayPage.locator("#f-mail").fill(server.ui_invitation_email);
      await replayPage.locator("#f-code").fill(server.ui_invitation_code);
      const replayed = replayPage.waitForResponse(candidate => {
        const url = new URL(candidate.url());
        return url.pathname === "/api/access/redeem" && candidate.request().method() === "POST";
      });
      await replayPage.getByRole("button", { name: "进入", exact: true }).click();
      const replayResponse = await replayed;
      assert(replayResponse.status() === 401, "consumed invitation replay was not rejected");
      const replayPayload = await replayResponse.json();
      assert(replayPayload.error === "invalid_credentials" && replayPayload.message === "邮箱或邀请码无效。", "invitation replay leaked a distinct failure reason");
      assert(await replayPage.locator("#f-code").inputValue() === "", "replayed invitation secret remained in the form");
      await assertNoAccessCookie(replayContext, server.origin, "invitation replay");
    } finally {
      await replayContext.close();
    }

    await restoredPage.setViewportSize({ width: 1240, height: 1080 });
    const loggedOut = restoredPage.waitForResponse(candidate => {
      const url = new URL(candidate.url());
      return url.pathname === "/api/access/logout" && candidate.request().method() === "POST";
    });
    await restoredPage.locator("#access-logout").click();
    const logoutResponse = await loggedOut;
    assert(logoutResponse.status() === 204, "logout did not return its empty success response");
    await restoredPage.getByRole("button", { name: "登录", exact: true }).waitFor({ state: "visible" });
    await restoredPage.getByText("已退出研究预览会话。", { exact: true }).waitFor({ state: "visible" });
    await assertNoAccessCookie(invitationContext, server.origin, "logout");
    const afterLogout = await invitationContext.request.get(`${server.origin}/api/console`);
    assert(afterLogout.status() === 401, "logged-out context retained protected console access");
    await captureAccessScenario(restoredPage, "logged-out public state", "logged-out", manifestEntries);
  } finally {
    await invitationContext.close();
  }

  const guestContext = await newGateContext(browser, { viewport: { width: 1240, height: 1080 } });
  try {
    const page = await guestContext.newPage();
    await openPublicRoot(page, server.origin);
    await page.getByRole("button", { name: "以访客身份浏览演示数据", exact: true }).click();
    await page.getByText("访客只读模式", { exact: true }).waitFor({ state: "visible" });
    assert(await page.locator("#view-data-boundary").getAttribute("data-source") === "demo", "guest surface lost its demo-data boundary");
    await assertNoAccessCookie(guestContext, server.origin, "guest demo");
    const protectedResponse = await guestContext.request.get(`${server.origin}/api/console`);
    assert(protectedResponse.status() === 401, "guest demo crossed the protected console boundary");
    await captureAccessScenario(page, "guest demo boundary", "guest-demo", manifestEntries);
  } finally {
    await guestContext.close();
  }

  assertInvitationSecretsNotPersisted(server);
  assert(manifestEntries.length === 10, `access evidence expected 10 screenshots, got ${manifestEntries.length}`);
  assert(new Set(manifestEntries.map(entry => entry.file)).size === 10, "access evidence screenshot names were not unique");
  const manifest = {
    schema_version: "1.0",
    artifact_kind: "matharc-browser-access-evidence",
    generated_at: new Date().toISOString(),
    page_identity: "MathArc research preview access and console",
    browser: "chromium",
    font_mode: FONT_MODE,
    review_result: "PASS",
    review_note: "PASS here means every capture passed the gate's layout assertions (no vertical text wrap in nav controls, prohibition cards intact, reveal completed, anchors under the sticky nav). It is not a human visual review.",
    captures: manifestEntries,
  };
  writeFileSync(join(ACCESS_EVIDENCE_DIR, "screenshot-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  return manifestEntries.length;
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

async function measureLandingProhibitionCards(page, label, width) {
  const metrics = await page.evaluate(() => {
    const section = document.querySelector(".nots");
    if (!section) return { missing: true };
    return {
      cards: [...section.children].map(card => {
        const icon = card.querySelector(":scope > .x");
        const content = card.querySelector(":scope > div");
        const title = content?.querySelector(":scope > b");
        const text = content?.querySelector(":scope > p");
        return {
          hasIcon: Boolean(icon),
          hasContent: Boolean(content),
          hasTitle: Boolean(title),
          hasText: Boolean(text),
          contentWidth: Math.round(content?.getBoundingClientRect().width || 0),
          titleHeight: Math.round(title?.getBoundingClientRect().height || 0),
          contentDisplay: content ? getComputedStyle(content).display : "missing",
        };
      }),
    };
  });
  assert(!metrics.missing, `${label} at ${width}px omitted the landing prohibition section`);
  assert(metrics.cards.length === 6, `${label} at ${width}px expected six landing prohibition cards, got ${metrics.cards.length}`);
  for (const [index, card] of metrics.cards.entries()) {
    assert(
      card.hasIcon && card.hasContent && card.hasTitle && card.hasText,
      `${label} at ${width}px prohibition card ${index + 1} lost its icon/text structure`,
    );
    assert(card.contentDisplay !== "grid", `${label} at ${width}px prohibition card ${index + 1} leaked its grid layout into nested text`);
    assert(card.contentWidth >= 96, `${label} at ${width}px prohibition card ${index + 1} text column collapsed to ${card.contentWidth}px`);
    assert(card.titleHeight <= 48, `${label} at ${width}px prohibition card ${index + 1} title wrapped vertically (${card.titleHeight}px)`);
  }
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

/* Copy quality at runtime: machine identifiers or rendering leftovers must not reach visible prose.
   Text inside .mono/.hash/code/kbd containers and form controls is the declared place for identifiers. */
async function scanCopyQuality(page, label) {
  const hits = await page.evaluate(({ allowed, containers }) => {
    const finder = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || parent.closest(containers)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const bad = [];
    while (finder.nextNode()) {
      const text = finder.currentNode.textContent || "";
      if (!/[㐀-鿿]/.test(text)) continue;
      const leak = text.match(/(?<![\w./-])(?:[a-z][a-z0-9]*(?:_[a-z0-9]+)+|[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)(?![\w./-])/);
      if (leak && !allowed.includes(leak[0])) bad.push({ kind: "raw-identifier", sample: leak[0], text: text.trim().slice(0, 80) });
      const leftover = text.match(/\b(?:undefined|NaN|TODO|TBD)\b|\[object Object\]/);
      if (leftover) bad.push({ kind: "placeholder-token", sample: leftover[0], text: text.trim().slice(0, 80) });
    }
    return bad;
  }, { allowed: [...COPY_ALLOW_IDENTIFIERS], containers: COPY_CONTAINER_SELECTOR });
  assert(hits.length === 0, `${label} shows machine text as prose: ${JSON.stringify(hits[0])}`);
}

/* Short inline controls (nav links, pills, buttons in a row) must stay on one line.  The 2026-09-03
   mobile capture had every landing nav label wrapped into a vertical column of characters while its
   manifest still said PASS — a screenshot nobody measured is not evidence. */
async function assertSingleLineControls(page, selector, label) {
  const tall = await page.evaluate(selector => {
    return [...document.querySelectorAll(selector)].filter(node => {
      const style = getComputedStyle(node);
      if (style.display === "none" || style.visibility === "hidden") return false;
      const rect = node.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return false;
      const lineHeight = parseFloat(style.lineHeight) || parseFloat(style.fontSize) * 1.5;
      const singleLine = lineHeight + parseFloat(style.paddingTop) + parseFloat(style.paddingBottom)
        + parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);
      // a second text line adds one full line-height on top of the single-line box
      return rect.height >= singleLine + lineHeight * 0.8;
    }).map(node => ({ text: node.textContent.trim().slice(0, 30), height: Math.round(node.getBoundingClientRect().height) }));
  }, selector);
  assert(tall.length === 0, `${label} wrapped a single-line control onto several lines: ${JSON.stringify(tall[0])}`);
}

async function captureLandingScene(page, scene, basename, manifestEntries) {
  mkdirSync(LANDING_EVIDENCE_DIR, { recursive: true });
  await settleVisualLayout(page);
  const viewport = page.viewportSize();
  const outputPath = join(LANDING_EVIDENCE_DIR, `${basename}.png`);
  const capturedAt = new Date().toISOString();
  await page.screenshot({ path: outputPath, fullPage: false });
  const digest = createHash("sha256").update(readFileSync(outputPath)).digest("hex");
  manifestEntries.push({
    file: relative(ROOT, outputPath),
    sha256: digest,
    scenario: scene,
    page_identity: { title: await page.title(), path: new URL(page.url()).pathname, view: "landing" },
    browser: "chromium",
    viewport,
    font_mode: FONT_MODE,
    color_scheme: await page.evaluate(() => document.documentElement.getAttribute("data-theme") || "light"),
    captured_at: capturedAt,
    review_result: "PASS",
  });
}

/* The landing page is a scroll experience, so the gate walks it instead of only rendering it:
   sticky nav with the current section marked, anchors landing below the nav, reveal completing
   for everything in view, and nothing left hidden for readers who asked for reduced motion. */
async function testLandingScrollExperience(browser, server, manifestEntries) {
  const context = await newGateContext(browser, { viewport: { width: 1440, height: 900 } });
  try {
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.stack || error.message));
    await openPublicRoot(page, server.origin);
    await page.locator(".lp .hero h1").waitFor({ state: "visible" });
    assert(await page.locator(".lpnav").evaluate(node => getComputedStyle(node).position) === "sticky", "landing nav is not sticky");
    assert(await page.locator('.lp[data-scrolled="false"]').count() === 1, "landing did not start in the unscrolled state");
    await assertSingleLineControls(page, ".lpnav .links button, .lpnav .btn, .hero .bigbtn, .hero .pill", "landing/1440 header");
    await waitFor(
      async () => await page.evaluate(() => [...document.querySelectorAll('.hero [data-reveal]')].every(node => node.dataset.reveal === "in" && getComputedStyle(node).opacity === "1")),
      "hero reveal did not complete",
      3000,
    );
    assert(await page.locator(".hero > .card").isVisible(), "hero evidence card is missing");
    await captureLandingScene(page, "landing hero after reveal", "landing-hero-1440", manifestEntries);

    for (const section of LANDING_SECTIONS) {
      await page.locator(`.lpnav .links button[data-v="${section}"]`).click();
      await waitFor(
        async () => await page.evaluate(id => {
          const target = document.getElementById(`sec-${id}`);
          const nav = document.querySelector(".lpnav");
          if (!target || !nav) return false;
          const top = target.getBoundingClientRect().top, navBottom = nav.getBoundingClientRect().bottom;
          // a section near the end of the page cannot reach the nav once the document is scrolled to its maximum
          const atPageEnd = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2;
          return (top >= navBottom - 2 && top <= navBottom + 40) || (atPageEnd && top >= navBottom - 2);
        }, section),
        `anchor ${section} did not land below the sticky nav`,
        4000,
      );
      assert(await page.locator('.lp[data-scrolled="true"]').count() === 1, `scrolling to ${section} did not mark the nav as scrolled`);
      const current = await page.locator('.lpnav .links button[aria-current="true"]').evaluateAll(nodes => nodes.map(node => node.dataset.v));
      assert(current.length === 1 && current[0] === section, `nav did not mark ${section} as current: ${JSON.stringify(current)}`);
      await waitFor(
        async () => await page.evaluate(id => {
          const target = document.getElementById(`sec-${id}`);
          const viewportHeight = window.innerHeight;
          return [...target.querySelectorAll('[data-reveal]')].filter(node => node.getBoundingClientRect().top < viewportHeight * 0.9)
            .every(node => node.dataset.reveal === "in" && getComputedStyle(node).opacity === "1");
        }, section),
        `${section} content in view stayed hidden after scrolling`,
        3000,
      );
      await assertSingleLineControls(page, ".lpnav .links button", `landing/${section} nav`);
      if (section === "how") await captureLandingScene(page, "landing section after anchor scroll", "landing-how-1440", manifestEntries);
      if (section === "nots") await captureLandingScene(page, "landing closing band", "landing-nots-1440", manifestEntries);
    }
    await measureLandingProhibitionCards(page, "landing/1440", 1440);
    await scanChineseEnglish(page, "landing/1440");
    await scanCopyQuality(page, "landing/1440");

    await page.locator("#themebtn2").click();
    assert(await page.evaluate(() => document.documentElement.getAttribute("data-theme")) === "dark", "landing theme toggle did not switch to dark");
    await page.evaluate(() => window.scrollTo(0, 0));
    await waitFor(async () => await page.locator('.lp[data-scrolled="false"]').count() === 1, "scrolling back to top did not clear the scrolled state", 3000);
    await captureLandingScene(page, "landing hero in dark theme", "landing-hero-1440-dark", manifestEntries);
    await page.locator("#themebtn2").click();
    assert(pageErrors.length === 0, `landing page errors: ${pageErrors.join("\n")}`);
  } finally {
    await context.close();
  }

  const mobile = await newGateContext(browser, { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  try {
    const page = await mobile.newPage();
    await openPublicRoot(page, server.origin);
    await page.locator(".lp .hero h1").waitFor({ state: "visible" });
    await assertSingleLineControls(page, ".lpnav .brand .mark, .lpnav .btn, .hero .bigbtn", "landing/390 header");
    assert(await page.locator(".lpnav .links").evaluate(node => getComputedStyle(node).display) === "none", "mobile landing still shows the desktop section links");
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), "mobile landing scrolls horizontally");
    await waitFor(
      async () => await page.evaluate(() => [...document.querySelectorAll('.hero [data-reveal]')].filter(node => node.getBoundingClientRect().top < window.innerHeight).every(node => node.dataset.reveal === "in")),
      "mobile hero reveal did not complete",
      3000,
    );
    await captureLandingScene(page, "landing hero on a phone", "landing-hero-390", manifestEntries);
    await measureLandingProhibitionCards(page, "landing/390", 390);
    await scanCopyQuality(page, "landing/390");
  } finally {
    await mobile.close();
  }

  const reduced = await newGateContext(browser, { viewport: { width: 1240, height: 900 }, reducedMotion: "reduce" });
  try {
    const page = await reduced.newPage();
    await openPublicRoot(page, server.origin);
    await page.locator(".lp .hero h1").waitFor({ state: "visible" });
    assert(await page.locator('[data-reveal]').count() === 0, "reduced-motion readers still received reveal attributes");
    const hidden = await page.evaluate(() => [...document.querySelectorAll(".sec > h2, .planecard, .step, .nots > div")].filter(node => getComputedStyle(node).opacity !== "1").length);
    assert(hidden === 0, `reduced-motion landing left ${hidden} elements transparent`);
    await page.locator('.lpnav .links button[data-v="case"]').click();
    await waitFor(async () => await page.evaluate(() => document.getElementById("sec-case").getBoundingClientRect().top <= document.querySelector(".lpnav").getBoundingClientRect().bottom + 40), "reduced-motion anchor did not land", 3000);
  } finally {
    await reduced.close();
  }
}

async function writeLandingManifest(manifestEntries) {
  assert(manifestEntries.length === 5, `landing evidence expected 5 screenshots, got ${manifestEntries.length}`);
  const manifest = {
    schema_version: "1.0",
    artifact_kind: "matharc-browser-landing-evidence",
    generated_at: new Date().toISOString(),
    page_identity: "MathArc landing page scroll experience",
    browser: "chromium",
    font_mode: FONT_MODE,
    review_result: "PASS",
    review_note: "PASS means the scroll-experience assertions held for every capture (sticky nav state, anchor offset, reveal completion, single-line controls, reduced-motion visibility). A human still reviews hierarchy and wording.",
    captures: manifestEntries,
  };
  writeFileSync(join(LANDING_EVIDENCE_DIR, "landing-screenshot-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
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

async function testWorkbenchStates(page) {
  await renderCase(page, "c7", { name: "workbench-state-ready", view: "workbench" });
  assert((await page.locator("body").innerText()).includes("从一个问题到一份可审结果"), "workbench ready state omitted the end-to-end heading");
  for (const [state, marker] of [["loading", "正在读取工作区"], ["empty", "还没有可展示的研究运行"], ["error", "工作区载荷无法使用"]]) {
    await dispatch(page, "wb-state", { v: state });
    assert((await page.locator("body").innerText()).includes(marker), `workbench ${state} state was not stable`);
  }
  await dispatch(page, "wb-state", { v: "ready" });
  assert((await page.locator("body").innerText()).includes("输入 → 拆解 → 调用 → 验证 → 证据"), "workbench did not recover to ready state");
}

async function testWorkbenchOwnership(page) {
  await renderCase(page, "c7", { name: "workbench-ownership", view: "workbench" });
  const plane = await page.locator("#planes button.on").innerText();
  assert(plane.includes("攻克过程"), "workbench did not highlight the attack plane");
  const navText = await page.locator("#nav").innerText();
  assert(navText.includes("演示工作台"), "attack-plane navigation omitted the workbench");
  await dispatch(page, "plane", { v: "p" });
  assert(!(await page.locator("#nav").innerText()).includes("演示工作台"), "topic-intelligence navigation still owns the workbench");
  await dispatch(page, "plane", { v: "d" });
  assert((await page.locator("#planes button.on").innerText()).includes("攻克过程"), "attack-plane navigation did not recover");
}

async function testMobileViewports(browser, server, accessCookies) {
  for (const viewport of MOBILE_VIEWPORTS) {
    const context = await newGateContext(browser, {
      viewport: { width: viewport.width, height: viewport.height },
      isMobile: true,
      hasTouch: true,
      deviceScaleFactor: 2,
      storageState: { cookies: accessCookies, origins: [] },
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.stack || error.message));
    try {
      const initialSnapshotResponse = page.waitForResponse(response => {
        const url = new URL(response.url());
        return url.pathname === "/api/runtime/snapshot" && response.request().method() === "GET";
      });
      await page.goto(`${server.origin}/`, { waitUntil: "domcontentloaded" });
      assert((await initialSnapshotResponse).status() === 200, `${viewport.name} did not authenticate its initial runtime snapshot`);
      assert(await page.evaluate(() => window.MathArcConsole.loadExport("/api/console")), `${viewport.name} could not load its authenticated console export`);
      await page.locator("#console-provenance").waitFor({ state: "attached" });
      // Start the mobile matrix from an explicit demo baseline.  A failed
      // refresh intentionally preserves the last live snapshot at runtime;
      // this matrix is testing demo rendering, so clear that snapshot first.
      const fellBackToDemo = await page.evaluate(() => {
        window.MathArcConsole.clear();
        return window.MathArcConsole.loadExport("/missing-console.json");
      });
      assert(!fellBackToDemo, `${viewport.name} did not enter its declared demo-data baseline`);
      for (const campaignId of CAMPAIGNS) {
        for (const testCase of VIEW_CASES) {
          await renderCase(page, campaignId, testCase);
          await measureBalance(page, `${viewport.name}/${campaignId}/${testCase.name}`, viewport.width);
          if (testCase.view === "landing") await measureLandingProhibitionCards(page, `${viewport.name}/${campaignId}/${testCase.name}`, viewport.width);
          await scanChineseEnglish(page, `${viewport.name}/${campaignId}/${testCase.name}`);
          await scanCopyQuality(page, `${viewport.name}/${campaignId}/${testCase.name}`);
        }
      }
      await testKeyboardControls(page);
      await testWorkbenchStates(page);
      assert(pageErrors.length === 0, `${viewport.name} page errors: ${pageErrors.join("\n")}`);
    } finally {
      await context.close();
    }
  }
}

async function testStartFlow(page) {
  // Start-flow assertions exercise the local demo portfolio. Clear the
  // authenticated live projection first so an absent candidate-problems
  // projection cannot replace the nine-gate demo with a fail-closed empty
  // surface.
  await page.evaluate(() => window.MathArcConsole.clear());
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
  // Tamper assertions exercise the sealed demo ledger.  Clear any live
  // projection left by earlier runtime checks so the live proofchain renderer
  // cannot replace the deterministic fixture on this shared page.
  await page.evaluate(() => {
    if (window.MathArcConsole && typeof window.MathArcConsole.clear === "function") window.MathArcConsole.clear();
    S.consolePayload = null;
    S.consolePayloadState = {status:"unloaded", projections:{}, reason:"tamper-fixture"};
    S.workbenchResult = null;
    S.compiled = false;
    S.guest = true;
  });
  await page.evaluate(() => {
    S.cid = "c7";
    S.tamper = null;
    S.chainActor = "*";
    S.chainSubj = "*";
    S.chainRound = "*";
    S.chainOpen = 0;
    S.plane = "v";
    S.view = "proofchain";
    render();
  });
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
    workbench: exportPayload.workspace.trace.claims.length,
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
  const initialResponse = await page.context().request.get(`${server.origin}/api/console`);
  assert(initialResponse.status() === 200, "M1 authenticated fixture could not read the initial console export");
  const initial = await initialResponse.json();
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
    return url.pathname === "/api/runtime/snapshot" && response.request().method() === "GET";
  });
  const mutation = server.campaignMutation();
  assert(mutation.tail > initialTail, "M1 workspace mutation did not append a new event");
  const refreshResponse = await refreshed;
  assert(refreshResponse.status() === 200, "M1 event refresh did not receive a console export");
  const refreshedSnapshot = await refreshResponse.json();
  const refreshedPayload = refreshedSnapshot && refreshedSnapshot.payload
    ? refreshedSnapshot.payload
    : refreshedSnapshot;
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
  return `emitted event ${mutation.tail}, refreshed /api/runtime/snapshot, and reconnected with after=${mutation.tail}`;
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
  assert(VIEW_CASES.length === 53, `case inventory must remain 53 views, got ${VIEW_CASES.length}`);
  const declaredViews = new Set([...PAGE_SOURCE.matchAll(/\bV\.([A-Za-z_][A-Za-z0-9_]*)\s*=/g)].map(match => match[1]));
  const coveredViews = new Set(VIEW_CASES.map(testCase => testCase.view));
  for (const view of declaredViews) assert(coveredViews.has(view), `declared view ${view} has no browser case`);

  const playwright = loadPlaywright();
  const server = await startServer();
  const browser = await playwright.chromium.launch({ headless: true });
  let accessCaptureCount = 0;
  const context = await newGateContext(browser, { viewport: { width: WIDTHS[0], height: 1080 } });
  const page = await context.newPage();
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
    assertInvitationSecretsNotPersisted(server);
    accessCaptureCount = await testAccessWorkflow(browser, server);
    const landingCaptures = [];
    await testLandingScrollExperience(browser, server, landingCaptures);
    await writeLandingManifest(landingCaptures);
    const authentication = await context.request.post(`${server.origin}/api/access/redeem`, {
      data: { email: server.gate_invitation_email, code: server.gate_invitation_code },
    });
    assert(authentication.status() === 200, "main browser context could not redeem its gate invitation");
    const authenticationPayload = await authentication.json();
    assert(
      authenticationPayload.authenticated === true
        && authenticationPayload.session.email === server.gate_invitation_email,
      "main browser context received the wrong authenticated session",
    );
    assertInvitationSecretsNotPersisted(server);
    const accessCookies = (await context.cookies(server.origin)).filter(cookie => cookie.name === ACCESS_COOKIE_NAME);
    assert(accessCookies.length === 1, "main browser context did not retain exactly one access cookie");
    const exportResponse = await context.request.get(`${server.origin}/api/console`);
    assert(exportResponse.status() === 200, "authenticated initial console export fetch failed");
    const exportPayload = await exportResponse.json();
    const restoredSession = page.waitForResponse(response => {
      const url = new URL(response.url());
      return url.pathname === "/api/access/session" && response.request().method() === "GET";
    });
    const initialSnapshot = page.waitForResponse(response => {
      const url = new URL(response.url());
      return url.pathname === "/api/runtime/snapshot" && response.request().method() === "GET";
    });
    await page.goto(`${server.origin}/`, { waitUntil: "domcontentloaded" });
    assert((await restoredSession).status() === 200, "main browser page did not restore its authenticated session");
    assert((await initialSnapshot).status() === 200, "main browser page did not authenticate its initial runtime snapshot");
    assert(await page.evaluate(() => window.MathArcConsole.loadExport("/api/console")), "main browser page could not load its authenticated console export");
    await page.locator("#console-provenance").waitFor({ state: "attached" });
    const fellBackToDemo = await page.evaluate(() => window.MathArcConsole.loadExport("/missing-console.json"));
    assert(!fellBackToDemo, "prototype regression cases did not enter their declared demo-data baseline");
    for (const width of WIDTHS) {
      await page.setViewportSize({ width, height: 1080 });
      for (const campaignId of CAMPAIGNS) {
        for (const testCase of VIEW_CASES) {
          await renderCase(page, campaignId, testCase);
          await measureBalance(page, `${campaignId}/${testCase.name}`, width);
          if (testCase.view === "landing") await measureLandingProhibitionCards(page, `${campaignId}/${testCase.name}`, width);
          await scanChineseEnglish(page, `${campaignId}/${testCase.name}`);
          await scanCopyQuality(page, `${campaignId}/${testCase.name}`);
        }
      }
    }
    await testAccordions(page);
    await testStartFlow(page);
    await testWorkbenchOwnership(page);
    await testTampers(page);
    await testDataBoundaryAndProvenance(page, server, exportPayload);
    await testM3LocalProjections(page, exportPayload);
    const m1 = await testM1SseAndReconnect(page, server, eventCursors);
    const m2 = await testM2ReviewWorkflow(page, server);
    await testMobileViewports(browser, server, accessCookies);
    assert(pageErrors.length === 0, `page errors: ${pageErrors.join("\n")}`);
    console.log(`access workflow passed: protected boundary, pending application, invalid/valid invite, Cookie restoration, replay rejection, logout, guest demo; ${accessCaptureCount} hash-bound screenshots`);
    console.log(`landing scroll experience passed: sticky nav state, ${LANDING_SECTIONS.length} anchors (${LANDING_SECTIONS.join(", ")}), reveal completion, single-line controls, reduced-motion visibility; ${landingCaptures.length} hash-bound screenshots (font mode ${FONT_MODE})`);
    console.log(`console browser gate passed: ${VIEW_CASES.length} cases x ${CAMPAIGNS.length} campaigns x ${WIDTHS.length} widths`);
    console.log(`mobile viewport checks passed: ${MOBILE_VIEWPORTS.map(viewport => `${viewport.name}=${viewport.width}x${viewport.height}`).join(", ")}`);
    console.log("keyboard checks passed: tabindex disclosures activated with Enter and Space");
    console.log(`M1 SSE workflow: ${m1}`);
    console.log(`M2 review workflow: ${m2}`);
  } finally {
    await context.close();
    await browser.close();
    await server.close();
  }
}

main().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
