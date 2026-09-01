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
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const ROOT = resolve(import.meta.dirname, "..");
const PAGE_PATH = resolve(ROOT, "docs/prototypes/problem-intel-console.html");
const PAGE_SOURCE = readFileSync(PAGE_PATH, "utf8");
const WIDTHS = [1240, 1366, 1440, 1536, 1728, 1920];
const CAMPAIGNS = ["c7", "q6"];
const LIVE_VIEWS = new Set(["source", "dag", "proofchain", "tools", "reasoning", "admin_roles", "campaign"]);
const PROCESS_SCOPED = new Set([
  "campaign", "exploration", "conjecture", "routes", "dag", "proofchain", "tools", "reasoning", "novelty", "disclosure",
]);

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

function buildConsoleExport() {
  const directory = mkdtempSync(join(tmpdir(), "matharc-console-browser-"));
  const output = join(directory, "console.json");
  const program = String.raw`
import json
import sys
from pathlib import Path
from matharc.v02.budget import BudgetLedger
from matharc.v02.campaign import ResearchCampaign
from matharc.v02.console_export import build_console_export
from matharc.v02.workspace import ResearchWorkspace
from matharc.v02.workspace_bundle import write_full_workspace_bundle
from matharc.v02.workers import StaticProposalWorker

root = Path(sys.argv[1]) / "workspace"
write_full_workspace_bundle(root)
workspace = ResearchWorkspace.load(root)
campaign = ResearchCampaign(workspace.trace, [StaticProposalWorker("prover", {})], budget=BudgetLedger(wall_seconds_limit=0.0))
workspace.record_campaign_result(campaign, campaign.run())
workspace.save()
Path(sys.argv[2]).write_text(json.dumps(build_console_export(root)), encoding="utf-8")
`;
  const completed = spawnSync(process.env.PYTHON || "python3", ["-c", program, directory, output], {
    cwd: ROOT,
    encoding: "utf8",
    env: { ...process.env, PYTHONPATH: [ROOT, process.env.PYTHONPATH].filter(Boolean).join(":") },
  });
  if (completed.status !== 0) {
    rmSync(directory, { recursive: true, force: true });
    fail(`could not build a real console export: ${completed.stderr || completed.stdout}`);
  }
  return { directory, json: readFileSync(output, "utf8") };
}

async function startServer(exportJson) {
  let serveExport = false;
  const reviewPosts = [];
  const server = createServer((request, response) => {
    const pathname = new URL(request.url || "/", "http://localhost").pathname;
    if (pathname === "/" || pathname === `/${basename(PAGE_PATH)}`) {
      response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
      response.end(PAGE_SOURCE);
      return;
    }
    if (pathname === "/console.json" && serveExport) {
      response.writeHead(200, { "content-type": "application/json" });
      response.end(exportJson);
      return;
    }
    if (pathname === "/api/review" && request.method === "POST") {
      const chunks = [];
      request.on("data", chunk => chunks.push(chunk));
      request.on("end", () => {
        reviewPosts.push({ authorization: request.headers.authorization || "", body: Buffer.concat(chunks).toString("utf8") });
        response.writeHead(201, { "content-type": "application/json" });
        response.end(JSON.stringify({ submitted: true, evidence_id: "EV-BROWSER-REVIEW" }));
      });
      return;
    }
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("not found");
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert(address && typeof address !== "string", "local browser fixture server did not bind");
  return {
    origin: `http://127.0.0.1:${address.port}`,
    enableExport() { serveExport = true; },
    reviewPosts() { return reviewPosts.slice(); },
    close() { return new Promise(resolve => server.close(resolve)); },
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

  server.enableExport();
  const loaded = await page.evaluate(() => window.MathArcConsole.loadExport("/console.json"));
  assert(loaded, "real console export was rejected by the browser bridge");
  const expected = {
    source: exportPayload.source_topic.source_claims.length,
    dag: exportPayload.workspace.trace.claims.length,
    proofchain: exportPayload.workspace.events.events.length,
    tools: exportPayload.workspace.trace.tool_calls.length,
    reasoning: exportPayload.workspace.trace.public_reasoning.length,
    admin_roles: Object.keys(exportPayload.role_policy.grants).length,
    campaign: exportPayload.campaign.report.rounds.length,
  };
  for (const [view, count] of Object.entries(expected)) {
    await renderCase(page, "c7", { name: `${view}-live`, view });
    const text = await page.locator("body").innerText();
    assert(await page.locator("#view-data-boundary").evaluate(node => node.dataset.source === "live"), `${view} retained a demo label after a declared live export`);
    assert(text.includes(String(count)), `${view} has no browser-visible numeric value derived from its real JSON count ${count}`);
  }
  for (const view of ["portfolio", "difficulty", "acct_usage"]) {
    await renderCase(page, "c7", { name: `${view}-unwired`, view });
    assert(await page.locator("#view-data-boundary").evaluate(node => node.dataset.source === "demo"), `${view} is not declared live but its demo label disappeared`);
  }
}

async function testM2ReviewPostExtension(page, server) {
  const result = await page.evaluate(async origin => {
    const input = document.createElement("input");
    input.type = "password";
    input.value = "browser-review-token";
    document.body.appendChild(input);
    try {
      const payload = await window.MathArcConsole.submitReview(`${origin}/api/review`, { review_id: "R-browser", verdict: "APPROVE" }, input);
      const cleared = input.value === "";
      const foreign = document.createElement("input");
      foreign.type = "password";
      foreign.value = "never-sent";
      let rejectedForeign = false;
      try {
        await window.MathArcConsole.submitReview("https://example.test/api/review", {}, foreign);
      } catch (error) {
        rejectedForeign = /same-origin/.test(String(error.message));
      }
      return { payload, cleared, rejectedForeign };
    } finally {
      input.remove();
    }
  }, server.origin);
  assert(result.payload && result.payload.submitted === true, "M2 review adapter did not expose the successful POST response");
  assert(result.cleared, "M2 review adapter retained the password token after POST");
  assert(result.rejectedForeign, "M2 review adapter accepted a cross-origin endpoint");
  const posts = server.reviewPosts();
  assert(posts.length === 1, `M2 review adapter sent ${posts.length} POSTs instead of exactly one`);
  assert(posts[0].authorization === "Bearer browser-review-token", "M2 review POST omitted or changed its bearer token");
  assert(JSON.parse(posts[0].body).review_id === "R-browser", "M2 review POST changed the submitted review record");
  return "exercised: same-origin POST, response, token clearing, and foreign-endpoint rejection";
}

async function main() {
  assert(VIEW_CASES.length === 52, `case inventory must remain 52 views, got ${VIEW_CASES.length}`);
  const declaredViews = new Set([...PAGE_SOURCE.matchAll(/\bV\.([A-Za-z_][A-Za-z0-9_]*)\s*=/g)].map(match => match[1]));
  const coveredViews = new Set(VIEW_CASES.map(testCase => testCase.view));
  for (const view of declaredViews) assert(coveredViews.has(view), `declared view ${view} has no browser case`);

  const playwright = loadPlaywright();
  const exportFixture = buildConsoleExport();
  const exportPayload = JSON.parse(exportFixture.json);
  const server = await startServer(exportFixture.json);
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: WIDTHS[0], height: 1080 } });
  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(error.stack || error.message));
  try {
    await page.goto(`${server.origin}/`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(50);
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
    const m2 = await testM2ReviewPostExtension(page, server);
    assert(pageErrors.length === 0, `page errors: ${pageErrors.join("\n")}`);
    console.log(`console browser gate passed: ${VIEW_CASES.length} cases x ${CAMPAIGNS.length} campaigns x ${WIDTHS.length} widths`);
    console.log(`M2 review POST extension: ${m2}`);
  } finally {
    await browser.close();
    await server.close();
    rmSync(exportFixture.directory, { recursive: true, force: true });
  }
}

main().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
