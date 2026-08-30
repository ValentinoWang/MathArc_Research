from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Mapping

from .metrics import compute_research_metrics
from .workspace import ResearchWorkspace


def _script_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")


def workspace_dashboard_payload(
    workspace: ResearchWorkspace,
    *,
    comparison: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "trace": workspace.trace.to_dict(),
        "metrics": compute_research_metrics(workspace.trace),
        "objects": workspace.objects.to_dict(),
        "sources": workspace.sources.to_dict(),
        "artifacts": workspace.artifacts.to_dict(),
        "events": workspace.events.to_dict(),
        "links": workspace.links_dict(),
        "audit": workspace.audit().to_dict(),
        "workspace": {
            "state_digest_sha256": workspace.state_digest(),
            "committed_state_digest_sha256": workspace.committed_state_digest,
            "strict_artifacts": workspace.strict_artifacts,
        },
        "comparison": dict(comparison or {}),
    }


def render_workspace_dashboard(
    workspace: ResearchWorkspace,
    output_path: str | Path,
    *,
    comparison: Mapping[str, Any] | None = None,
    title: str = "MathArc Research v0.2 · Research Workspace",
) -> Path:
    payload = workspace_dashboard_payload(workspace, comparison=comparison)
    template = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{color-scheme:dark;--bg:#06080e;--panel:#101522;--panel2:#151c2c;--line:#29344c;--text:#eff3ff;--muted:#9da9c6;--green:#6ee7b7;--cyan:#67e8f9;--amber:#fbbf24;--rose:#fb7185;--violet:#c4b5fd;--blue:#93c5fd}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 15% 0,#162035 0,#080b13 36%,#06080e 70%);color:var(--text);font:14px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}
header{padding:24px 28px 16px;border-bottom:1px solid var(--line);background:rgba(6,8,14,.88);position:sticky;top:0;z-index:20;backdrop-filter:blur(16px)} h1{font-size:23px;margin:0 0 6px}.sub{color:var(--muted);max-width:1200px}
main{max-width:1900px;margin:auto;padding:22px 28px 50px}.grid{display:grid;gap:14px}.kpis{grid-template-columns:repeat(auto-fit,minmax(170px,1fr));margin-bottom:14px}.layout{grid-template-columns:minmax(0,1.35fr) minmax(360px,.65fr)}@media(max-width:1100px){.layout{grid-template-columns:1fr}main,header{padding-left:14px;padding-right:14px}}
.card{background:linear-gradient(180deg,rgba(20,27,43,.98),rgba(12,16,26,.98));border:1px solid var(--line);border-radius:14px;padding:15px;box-shadow:0 18px 55px rgba(0,0,0,.2)}.kpi .label,.muted{color:var(--muted)}.kpi .value{font-size:25px;font-weight:760;margin-top:3px;overflow-wrap:anywhere}.section{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 12px;font-size:16px}
.badge{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:2px 8px;font-size:11px;font-weight:750}.PROVED,.VERIFIED,.PASS,.CLOSED{color:var(--green);border-color:rgba(110,231,183,.4);background:rgba(110,231,183,.08)}.REFUTED,.FALSIFIED,.REJECTED,.FAIL,.RETRACTED{color:var(--rose);border-color:rgba(251,113,133,.42);background:rgba(251,113,133,.08)}.BLOCKED,.ERROR,.PENDING{color:var(--amber);border-color:rgba(251,191,36,.4);background:rgba(251,191,36,.08)}.CANDIDATE,.ACTIVE,.RUNNING,.DEFINED{color:var(--cyan);border-color:rgba(103,232,249,.38);background:rgba(103,232,249,.08)}.OPEN,.PROPOSED{color:var(--violet)}
.graph-wrap{overflow:auto;min-height:360px;border:1px solid #202a3e;border-radius:11px;background:#090d16}.graph-wrap svg{display:block;min-width:780px}.node rect{fill:#141c2c;stroke:#35425e;stroke-width:1.2}.node text{fill:#f4f6ff;font-size:11px}.node .id{fill:var(--blue);font-weight:700}.node.PROVED rect{stroke:var(--green)}.node.REFUTED rect{stroke:var(--rose)}.node.BLOCKED rect{stroke:var(--amber)}.node.CANDIDATE rect{stroke:var(--cyan)}.edge{stroke:#53627e;stroke-width:1.15;marker-end:url(#arrow)}
.metric{display:grid;grid-template-columns:190px 1fr 55px;gap:9px;align-items:center;margin:8px 0}.bar{height:8px;background:#222b3e;border-radius:99px;overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--violet),var(--cyan));border-radius:99px}
.scroll{overflow:auto;max-height:430px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-weight:650;position:sticky;top:0;background:var(--panel);z-index:2}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;color:#d9e5ff;overflow-wrap:anywhere}.small{font-size:12px}
.timeline{border-left:1px solid #384761;margin-left:7px;padding-left:18px}.event{position:relative;margin:0 0 15px}.event:before{content:"";position:absolute;left:-23px;top:6px;width:9px;height:9px;border-radius:50%;background:var(--cyan);box-shadow:0 0 0 4px var(--panel)}.event h4{margin:0 0 4px}.kv{display:grid;grid-template-columns:125px 1fr;gap:4px 9px}.kv b{color:var(--muted);font-weight:600}
.matrix{overflow:auto}.matrix table td.center,.matrix table th.center{text-align:center}.dot{display:inline-block;width:11px;height:11px;border-radius:50%;background:#2b354a}.dot.on{background:var(--green);box-shadow:0 0 0 3px rgba(110,231,183,.1)}
.callout{border:1px solid rgba(103,232,249,.3);background:rgba(8,145,178,.07);border-radius:10px;padding:11px}.callout.warn{border-color:rgba(251,191,36,.35);background:rgba(146,64,14,.09)}.callout.err{border-color:rgba(251,113,133,.38);background:rgba(127,29,29,.1)}.issue{border-left:3px solid var(--amber);padding:8px 10px;margin:8px 0;background:rgba(9,12,20,.5)}.issue.ERROR{border-left-color:var(--rose)}.issue.INFO{border-left-color:var(--blue)}
.route,.failure,.object{border:1px solid var(--line);border-radius:10px;padding:10px;margin:8px 0;background:rgba(8,11,18,.55)}.head{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}.chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}.chip{border:1px solid #29354d;color:var(--muted);border-radius:7px;padding:2px 6px;font-size:11px}.hash{font-size:10px;color:#8290ad;word-break:break-all}
footer{padding:15px 25px 35px;text-align:center;color:var(--muted)}
</style>
</head>
<body>
<header><h1>__TITLE__</h1><div class="sub" id="contract"></div></header>
<main>
<section class="grid kpis" id="kpis"></section>
<section class="grid layout">
<div class="grid">
  <article class="card"><h2 class="section">命题依赖图 <span class="muted small">边指向依赖它的命题</span></h2><div class="graph-wrap" id="claim-graph"></div></article>
  <article class="card"><h2 class="section">独立证据矩阵</h2><div class="matrix" id="evidence-matrix"></div></article>
  <article class="card"><h2 class="section">公开研究轨迹 <span class="muted small">目标—前提—动作—观察—证伪—决策</span></h2><div class="timeline" id="reasoning"></div></article>
  <article class="card"><h2 class="section">工具调用与冷重放</h2><div class="scroll"><table><thead><tr><th>Call</th><th>工具 / 目的</th><th>状态</th><th>命题</th><th>Replay</th></tr></thead><tbody id="tools"></tbody></table></div></article>
  <article class="card"><h2 class="section">事件哈希链</h2><div class="scroll"><table><thead><tr><th>#</th><th>事件</th><th>Actor</th><th>Subjects</th><th>Previous → Hash</th></tr></thead><tbody id="events"></tbody></table></div></article>
</div>
<div class="grid">
  <article class="card"><h2 class="section">研究质量指标</h2><div id="metrics"></div><div class="callout small" id="metric-note"></div></article>
  <article class="card"><h2 class="section">数学对象账本</h2><div id="objects"></div></article>
  <article class="card"><h2 class="section">文献命题账本</h2><div id="sources"></div></article>
  <article class="card"><h2 class="section">路线与 Kill Tests</h2><div id="routes"></div></article>
  <article class="card"><h2 class="section">失败传播</h2><div id="failures"></div></article>
  <article class="card"><h2 class="section">内容寻址证据</h2><div class="scroll"><table><thead><tr><th>Artifact</th><th>Role</th><th>Claims</th><th>SHA-256</th></tr></thead><tbody id="artifacts"></tbody></table></div></article>
  <article class="card"><h2 class="section">对抗审计</h2><div id="audit"></div></article>
  <article class="card"><h2 class="section">基准资格</h2><div id="comparison"></div></article>
</div>
</section>
</main><footer>MathArc Research v0.2 · verifier-gated, tamper-evident research observability</footer>
<script id="workspace-data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('workspace-data').textContent),T=D.trace,M=D.metrics,A=D.audit;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=v=>`${(100*Number(v||0)).toFixed(1)}%`, short=v=>String(v||'').slice(0,12), badge=v=>`<span class="badge ${esc(v)}">${esc(v)}</span>`;
document.getElementById('contract').innerHTML=`<b>${esc(T.contract.problem)}</b><br>${esc(T.contract.scope)}<br><code>${esc(D.workspace.state_digest_sha256)}</code>`;
const k=[['Release',M.release_state,0],['Target closure',M.target_logical_closure,1],['Critical path',M.critical_path_closure,1],['Audit',A.valid?'PASS':'FAIL',0],['Events',D.events.events.length,0],['Artifacts',D.artifacts.records.length,0],['Objects',D.objects.objects.length,0],['Open critical',M.open_critical_obligations.length,0]];
document.getElementById('kpis').innerHTML=k.map(x=>`<div class="card kpi"><div class="label">${esc(x[0])}</div><div class="value">${x[2]?pct(x[1]):esc(x[1])}</div></div>`).join('');

function graph(){const claims=T.claims,map=Object.fromEntries(claims.map(c=>[c.claim_id,c])),memo={};function depth(id){if(memo[id]!=null)return memo[id];const c=map[id];return memo[id]=(!c||!c.dependencies.length)?0:1+Math.max(...c.dependencies.map(depth))}const levels={};claims.forEach(c=>(levels[depth(c.claim_id)]??=[]).push(c));const ds=Object.keys(levels).map(Number),max=Math.max(0,...ds),w=Math.max(820,(max+1)*260),h=Math.max(350,...Object.values(levels).map(v=>v.length*115+70));const pos={};Object.entries(levels).forEach(([d,arr])=>arr.forEach((c,i)=>pos[c.claim_id]={x:45+Number(d)*250,y:42+i*110}));let edges='';claims.forEach(c=>c.dependencies.forEach(dep=>{const a=pos[dep],b=pos[c.claim_id];if(a&&b)edges+=`<path class="edge" d="M ${a.x+180} ${a.y+34} C ${a.x+215} ${a.y+34}, ${b.x-35} ${b.y+34}, ${b.x} ${b.y+34}"/>`}));let nodes=claims.map(c=>{const p=pos[c.claim_id],txt=c.statement.length>48?c.statement.slice(0,45)+'…':c.statement;return `<g class="node ${esc(c.status)}" transform="translate(${p.x},${p.y})"><rect width="180" height="68" rx="9"/><text class="id" x="10" y="18">${esc(c.claim_id)} · ${esc(c.status)}</text><text x="10" y="38">${esc(txt.slice(0,28))}</text><text x="10" y="54">${esc(txt.slice(28,56))}</text></g>`}).join('');return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#53627e"/></marker></defs>${edges}${nodes}</svg>`}document.getElementById('claim-graph').innerHTML=graph();

const groups=[...new Set(T.evidence.filter(e=>e.status==='ACCEPTED').map(e=>e.independence_group))].sort();let mh='<table><thead><tr><th>Claim</th>'+groups.map(g=>`<th class="center">${esc(g)}</th>`).join('')+'</tr></thead><tbody>';T.claims.forEach(c=>{const eg=new Set(c.evidence_ids.map(id=>T.evidence.find(e=>e.evidence_id===id)).filter(Boolean).map(e=>e.independence_group));mh+=`<tr><td><code>${esc(c.claim_id)}</code> ${badge(c.status)}</td>`+groups.map(g=>`<td class="center"><i class="dot ${eg.has(g)?'on':''}"></i></td>`).join('')+'</tr>'});document.getElementById('evidence-matrix').innerHTML=mh+'</tbody></table>';

const mkeys=['weighted_proof_closure','critical_path_closure','evidence_independence','independent_audit_coverage','cold_replay_rate','falsification_coverage','route_mechanism_diversity','public_trace_coverage','tool_transparency','boundary_integrity','research_readiness_index'];document.getElementById('metrics').innerHTML=mkeys.map(x=>`<div class="metric"><span>${esc(x.replaceAll('_',' '))}</span><div class="bar"><i style="width:${100*Math.max(0,Math.min(1,M[x]||0))}%"></i></div><code>${pct(M[x])}</code></div>`).join('');document.getElementById('metric-note').textContent=M.metric_semantics;

document.getElementById('reasoning').innerHTML=T.public_reasoning.map(s=>`<article class="event"><h4>${esc(s.step_id)} · ${esc(s.role)}</h4><div class="kv small"><b>目标</b><span>${esc(s.objective)}</span><b>前提</b><span>${s.premises.map(esc).join('；')}</span><b>动作</b><span>${esc(s.proposed_move)}</span><b>观察</b><span>${esc(s.observation)}</span><b>证伪</b><span>${esc(s.falsification_test)}</span><b>决策</b><span>${esc(s.decision)}</span></div></article>`).join('')||'<span class="muted">No public reasoning.</span>';
document.getElementById('tools').innerHTML=T.tool_calls.map(x=>`<tr><td><code>${esc(x.call_id)}</code></td><td><b>${esc(x.tool)}</b><br><span class="muted">${esc(x.purpose)}</span></td><td>${badge(x.status)}</td><td>${x.linked_claim_ids.map(esc).join(', ')}</td><td><code>${esc(x.replay_command||'—')}</code></td></tr>`).join('');
document.getElementById('events').innerHTML=D.events.events.map(x=>`<tr><td>${x.sequence}</td><td><code>${esc(x.event_id)}</code><br>${esc(x.event_type)}</td><td>${esc(x.actor)}</td><td>${x.subject_ids.map(esc).join(', ')}</td><td class="hash">${short(x.previous_hash)} → ${short(x.event_hash)}</td></tr>`).join('');

document.getElementById('objects').innerHTML=D.objects.objects.map(o=>`<article class="object"><div class="head"><b><code>${esc(o.symbol)}</code> · ${esc(o.name)}</b>${badge(o.status)}</div><div class="small">${esc(o.definition)}</div><div class="muted small">${esc(o.type_signature)} · ${esc(o.current_role)}</div><div class="chips">${o.dependencies.map(x=>`<span class="chip">depends ${esc(x)}</span>`).join('')}</div></article>`).join('');
document.getElementById('sources').innerHTML=D.sources.claims.map(s=>`<article class="object"><div class="head"><b>${esc(s.source_claim_id)}</b>${badge(s.status)}</div><div class="small">${esc(s.claimed_result)}</div><div class="muted small">${esc(s.bibliographic_citation)} · ${esc(s.pinned_version)} · ${esc(s.locator)}</div><div class="hash">${esc(s.source_digest_sha256)}</div></article>`).join('')||'<span class="muted">No source claims.</span>';
document.getElementById('routes').innerHTML=T.routes.map(r=>`<article class="route"><div class="head"><b>${esc(r.route_id)} · ${esc(r.name)}</b>${badge(r.status)}</div><div class="small">${esc(r.hypothesis)}</div><div class="muted small"><b>Kill:</b> ${esc(r.kill_test)}</div><div class="chips">${r.mechanism_signature.map(x=>`<span class="chip">${esc(x)}</span>`).join('')}</div></article>`).join('');
document.getElementById('failures').innerHTML=T.failures.map(f=>`<article class="failure"><div class="head"><b>${esc(f.failure_id)}</b>${badge(f.failure_class)}</div><div class="small"><b>诊断：</b>${esc(f.diagnosis)}</div><div class="small"><b>见证：</b>${esc(f.minimal_witness)}</div><div class="small"><b>修复：</b>${esc(f.repair)}</div><div class="muted small">失效：${f.invalidated_claim_ids.map(esc).join(', ')||'—'}</div></article>`).join('')||'<span class="muted">No failures.</span>';
document.getElementById('artifacts').innerHTML=D.artifacts.records.map(a=>`<tr><td><code>${esc(a.artifact_id)}</code></td><td>${esc(a.logical_role)}</td><td>${a.linked_claim_ids.map(esc).join(', ')}</td><td class="hash">${esc(a.sha256)}</td></tr>`).join('');

document.getElementById('audit').innerHTML=`<div class="callout ${A.valid?'':'err'}"><b>${A.valid?'PASS':'FAIL'}</b> · ${A.error_count} errors · ${A.warning_count} warnings<br><span class="hash">state ${esc(A.current_state_digest_sha256)}</span></div>`+A.issues.map(i=>`<div class="issue ${esc(i.severity)}"><b>${esc(i.severity)} · ${esc(i.category)}</b><div>${esc(i.message)}</div><div class="muted small">Repair: ${esc(i.repair)}</div></div>`).join('');
const C=D.comparison||{},ce=document.getElementById('comparison');if(!Object.keys(C).length)ce.innerHTML='<div class="callout warn small">尚无满足同题、同预算、配对、冷重放和统计下界的外部 Agent 比较；禁止输出“普遍更强”。</div>';else ce.innerHTML=`<div>${badge(C.qualification_state||'UNKNOWN')}</div><p class="small">paired=${esc(C.paired_case_count)} · claim allowed=${esc(C.superiority_claim_allowed)}</p><div class="muted small">${(C.reasons||[]).map(esc).join('；')}</div>`;
</script>
</body></html>"""
    document = template.replace("__TITLE__", html.escape(title)).replace(
        "__DATA__", _script_json(payload)
    )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(document, encoding="utf-8")
    return target
