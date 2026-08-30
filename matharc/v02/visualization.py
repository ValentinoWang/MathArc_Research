from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Mapping

from .metrics import compute_research_metrics
from .trace import ResearchTrace


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")


def dashboard_payload(
    trace: ResearchTrace,
    *,
    comparison: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "trace": trace.to_dict(),
        "metrics": compute_research_metrics(trace),
        "comparison": dict(comparison or {}),
    }


def render_research_dashboard(
    trace: ResearchTrace,
    output_path: str | Path,
    *,
    comparison: Mapping[str, Any] | None = None,
    title: str = "MathArc Research v0.2",
) -> Path:
    """Render a dependency-free, self-contained research dashboard."""

    payload = dashboard_payload(trace, comparison=comparison)
    serialized = _json_for_script(payload)
    safe_title = html.escape(title)
    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title}</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #07090f; --panel: #10141f; --panel2: #151b29; --line: #273044;
  --text: #edf1ff; --muted: #9ca8c4; --cyan: #67e8f9; --green: #6ee7b7;
  --amber: #fbbf24; --rose: #fb7185; --violet: #c4b5fd; --blue: #93c5fd;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: radial-gradient(circle at top left,#111827 0,#07090f 42%); color: var(--text); font: 14px/1.5 Inter, ui-sans-serif, system-ui, sans-serif; }}
header {{ padding: 28px 32px 18px; border-bottom: 1px solid var(--line); background: rgba(7,9,15,.86); position: sticky; top: 0; z-index: 5; backdrop-filter: blur(14px); }}
h1 {{ margin: 0 0 6px; font-size: 24px; letter-spacing: -.02em; }}
.sub {{ color: var(--muted); max-width: 1050px; }}
main {{ padding: 24px 32px 48px; max-width: 1700px; margin: 0 auto; }}
.grid {{ display: grid; gap: 16px; }}
.kpis {{ grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); margin-bottom: 16px; }}
.two {{ grid-template-columns: minmax(0,1.35fr) minmax(320px,.65fr); }}
@media(max-width:1000px) {{ .two {{ grid-template-columns: 1fr; }} main,header {{ padding-left:16px;padding-right:16px; }} }}
.card {{ background: linear-gradient(180deg,rgba(21,27,41,.98),rgba(13,17,27,.98)); border: 1px solid var(--line); border-radius: 14px; padding: 16px; box-shadow: 0 18px 50px rgba(0,0,0,.18); }}
.kpi .value {{ font-size: 27px; font-weight: 760; margin: 4px 0 2px; }}
.kpi .label,.muted {{ color: var(--muted); }}
.section-title {{ display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 12px;font-size:16px; }}
.badge {{ display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;padding:2px 8px;font-size:11px;font-weight:700;letter-spacing:.03em; }}
.PROVED,.PASS,.CLOSED {{ color:var(--green);border-color:rgba(110,231,183,.38);background:rgba(110,231,183,.08); }}
.REFUTED,.FALSIFIED,.FAIL,.RETRACTED {{ color:var(--rose);border-color:rgba(251,113,133,.4);background:rgba(251,113,133,.08); }}
.BLOCKED,.ERROR {{ color:var(--amber);border-color:rgba(251,191,36,.4);background:rgba(251,191,36,.08); }}
.CANDIDATE,.ACTIVE,.RUNNING {{ color:var(--cyan);border-color:rgba(103,232,249,.38);background:rgba(103,232,249,.08); }}
.OPEN,.PROPOSED,.REQUESTED {{ color:var(--violet); }}
.metric-row {{ display:grid;grid-template-columns:190px 1fr 58px;gap:10px;align-items:center;margin:9px 0; }}
.bar {{ height:9px;border-radius:999px;background:#20283a;overflow:hidden; }}
.bar > i {{ display:block;height:100%;background:linear-gradient(90deg,var(--violet),var(--cyan));border-radius:999px; }}
.claim {{ border:1px solid var(--line);background:rgba(9,12,20,.58);border-radius:11px;padding:12px;margin:9px 0; }}
.claim-head {{ display:flex;justify-content:space-between;gap:10px;align-items:flex-start; }}
.claim-id {{ color:var(--blue);font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-weight:700; }}
.claim-text {{ margin:5px 0;color:#f4f6ff; }}
.chips {{ display:flex;flex-wrap:wrap;gap:6px;margin-top:7px; }}
.chip {{ color:var(--muted);border:1px solid #222c40;border-radius:7px;padding:2px 6px;font-size:11px; }}
.route {{ border-left:3px solid var(--violet);padding:10px 12px;background:rgba(9,12,20,.55);border-radius:0 10px 10px 0;margin:10px 0; }}
.timeline {{ border-left:1px solid #33405b;margin-left:7px;padding-left:18px; }}
.step {{ position:relative;margin:0 0 16px; }}
.step:before {{ content:'';position:absolute;left:-23px;top:6px;width:9px;height:9px;border-radius:50%;background:var(--cyan);box-shadow:0 0 0 4px #10141f; }}
.step h4 {{ margin:0 0 4px; }}
.reason-grid {{ display:grid;grid-template-columns:130px 1fr;gap:5px 10px; }}
.reason-grid b {{ color:var(--muted);font-weight:600; }}
table {{ width:100%;border-collapse:collapse;font-size:12px; }}
th,td {{ text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top; }}
th {{ color:var(--muted);font-weight:600;position:sticky;top:0;background:var(--panel); }}
.scroll {{ overflow:auto;max-height:470px; }}
.failure {{ border:1px solid rgba(251,113,133,.24);border-radius:10px;padding:11px;margin:9px 0;background:rgba(127,29,29,.07); }}
.callout {{ border:1px solid rgba(103,232,249,.25);background:rgba(8,145,178,.06);padding:12px;border-radius:10px;color:#dffaff; }}
.warning {{ border-color:rgba(251,191,36,.3);background:rgba(146,64,14,.08);color:#fff2c5; }}
.small {{ font-size:12px; }}
code {{ color:#d8e4ff;font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
footer {{ color:var(--muted);padding:18px 32px 36px;text-align:center; }}
</style>
</head>
<body>
<header>
  <h1>{safe_title}</h1>
  <div class="sub" id="contract"></div>
</header>
<main>
  <section class="grid kpis" id="kpis"></section>
  <section class="grid two">
    <div class="grid">
      <div class="card"><h2 class="section-title">证明依赖图 <span class="muted small">Claim DAG</span></h2><div id="claims"></div></div>
      <div class="card"><h2 class="section-title">公开研究轨迹 <span class="muted small">可审计摘要，不是逐 token 私有思维链</span></h2><div class="timeline" id="timeline"></div></div>
      <div class="card"><h2 class="section-title">工具调用账本</h2><div class="scroll"><table><thead><tr><th>Call</th><th>工具 / 目的</th><th>状态</th><th>关联命题</th><th>冷重放</th></tr></thead><tbody id="tools"></tbody></table></div></div>
    </div>
    <div class="grid">
      <div class="card"><h2 class="section-title">研究质量指标</h2><div id="metrics"></div><div class="callout small" id="metric-note"></div></div>
      <div class="card"><h2 class="section-title">并行路线</h2><div id="routes"></div></div>
      <div class="card"><h2 class="section-title">失败学习</h2><div id="failures"></div></div>
      <div class="card"><h2 class="section-title">基准资格</h2><div id="comparison"></div></div>
      <div class="card"><h2 class="section-title">严格边界</h2><div id="boundary"></div></div>
    </div>
  </section>
</main>
<footer>MathArc Research v0.2 · proof-carrying research observability</footer>
<script id="matharc-data" type="application/json">{serialized}</script>
<script>
const D = JSON.parse(document.getElementById('matharc-data').textContent);
const T = D.trace, M = D.metrics, C = D.comparison || {{}};
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
const pct = value => `${{(100 * Number(value || 0)).toFixed(1)}}%`;
const badge = value => `<span class="badge ${{esc(value)}}">${{esc(value)}}</span>`;

document.getElementById('contract').innerHTML = `<b>${{esc(T.contract.problem)}}</b><br>${{esc(T.contract.scope)}}`;
const kpis = [
 ['Release state', M.release_state, false], ['Target closure', M.target_logical_closure, true],
 ['Critical path', M.critical_path_closure, true], ['Replay rate', M.cold_replay_rate, true],
 ['Open critical', M.open_critical_obligations.length, false], ['Boundary integrity', M.boundary_integrity, true]
];
document.getElementById('kpis').innerHTML = kpis.map(([label,value,isPct]) => `<div class="card kpi"><div class="label">${{esc(label)}}</div><div class="value">${{isPct?pct(value):esc(value)}}</div></div>`).join('');

const metricKeys = ['weighted_proof_closure','critical_path_closure','evidence_independence','independent_audit_coverage','cold_replay_rate','falsification_coverage','route_mechanism_diversity','public_trace_coverage','tool_transparency','boundary_integrity','research_readiness_index'];
document.getElementById('metrics').innerHTML = metricKeys.map(key => `<div class="metric-row"><span>${{esc(key.replaceAll('_',' '))}}</span><div class="bar"><i style="width:${{100*Math.max(0,Math.min(1,M[key]||0))}}%"></i></div><code>${{pct(M[key])}}</code></div>`).join('');
document.getElementById('metric-note').textContent = M.metric_semantics;

document.getElementById('claims').innerHTML = T.claims.map(claim => `<article class="claim"><div class="claim-head"><div><span class="claim-id">${{esc(claim.claim_id)}}</span> ${{claim.critical?'<span class="badge BLOCKED">CRITICAL</span>':''}}</div>${{badge(claim.status)}}</div><div class="claim-text">${{esc(claim.statement)}}</div><div class="muted small">Scope: ${{esc(claim.scope)}} · weight ${{esc(claim.weight)}}</div><div class="chips">${{claim.dependencies.map(x=>`<span class="chip">depends: ${{esc(x)}}</span>`).join('')}}${{claim.evidence_ids.map(x=>`<span class="chip">evidence: ${{esc(x)}}</span>`).join('')}}</div></article>`).join('') || '<div class="muted">No claims.</div>';

document.getElementById('routes').innerHTML = T.routes.map(route => `<article class="route"><div class="claim-head"><b>${{esc(route.route_id)}} · ${{esc(route.name)}}</b>${{badge(route.status)}}</div><div class="small">${{esc(route.hypothesis)}}</div><div class="muted small"><b>Kill test:</b> ${{esc(route.kill_test)}}</div><div class="chips">${{route.mechanism_signature.map(x=>`<span class="chip">${{esc(x)}}</span>`).join('')}}</div></article>`).join('') || '<div class="muted">No routes.</div>';

document.getElementById('timeline').innerHTML = T.public_reasoning.map(step => `<article class="step"><h4>${{esc(step.step_id)}} · ${{esc(step.role)}}</h4><div class="reason-grid small"><b>目标</b><span>${{esc(step.objective)}}</span><b>前提</b><span>${{step.premises.map(esc).join('；')}}</span><b>动作</b><span>${{esc(step.proposed_move)}}</span><b>观察</b><span>${{esc(step.observation)}}</span><b>证伪</b><span>${{esc(step.falsification_test)}}</span><b>决策</b><span>${{esc(step.decision)}}</span></div></article>`).join('') || '<div class="muted">No public reasoning steps.</div>';

document.getElementById('tools').innerHTML = T.tool_calls.map(call => `<tr><td><code>${{esc(call.call_id)}}</code></td><td><b>${{esc(call.tool)}}</b><br><span class="muted">${{esc(call.purpose)}}</span></td><td>${{badge(call.status)}}</td><td>${{call.linked_claim_ids.map(esc).join(', ')}}</td><td>${{call.replay_command?`<code>${{esc(call.replay_command)}}</code>`:'—'}}</td></tr>`).join('') || '<tr><td colspan="5" class="muted">No tool calls.</td></tr>';

document.getElementById('failures').innerHTML = T.failures.map(f => `<article class="failure"><div class="claim-head"><b>${{esc(f.failure_id)}}</b>${{badge(f.failure_class)}}</div><div class="small"><b>诊断：</b>${{esc(f.diagnosis)}}</div><div class="small"><b>最小见证：</b>${{esc(f.minimal_witness||'—')}}</div><div class="small"><b>修复：</b>${{esc(f.repair)}}</div><div class="muted small">失效节点：${{f.invalidated_claim_ids.map(esc).join(', ')||'—'}}</div></article>`).join('') || '<div class="muted">No recorded failures.</div>';

const comparison = document.getElementById('comparison');
if (!Object.keys(C).length) {{ comparison.innerHTML = '<div class="callout warning small">尚无同题、同预算、配对且可冷重放的基准结果；禁止输出“强于所有现有 Agent”。</div>'; }}
else {{ comparison.innerHTML = `<div>${{badge(C.qualification_state||'UNKNOWN')}}</div><p class="small">paired cases: ${{esc(C.paired_case_count)}} · claim allowed: ${{esc(C.superiority_claim_allowed)}}</p><div class="muted small">${{(C.reasons||[]).map(esc).join('；')}}</div>`; }}

const validation = M.validation;
document.getElementById('boundary').innerHTML = `<div class="callout ${{validation.valid?'':'warning'}} small"><b>Validation:</b> ${{validation.valid?'PASS':'FAIL'}}<br><b>Target claim allowed:</b> ${{M.marketing_claim_allowed?'YES':'NO'}}<br>${{esc(M.claim_boundary)}}</div>${{validation.errors.length?`<p class="small">Errors: ${{validation.errors.map(esc).join('；')}}</p>`:''}}${{validation.warnings.length?`<p class="small muted">Warnings: ${{validation.warnings.map(esc).join('；')}}</p>`:''}}`;
</script>
</body>
</html>
"""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(document, encoding="utf-8")
    return target
