# Public welcome page restoration

- Readback time: 2026-09-05 23:39 CST
- Root dashboard restored to `/opt/matharc-research/current/docs/prototypes/problem-intel-console.html`.
- `https://research.matharc.space/` now returns the MathArc welcome/landing surface with title `MathArc 数学研究工作台`, the research-preview invitation entry, and the prior landing copy.
- Root response: HTTP `200`, `464715` bytes.
- `/api/health`: HTTP `200`, workspace state digest `8aba2912a4dcd23f88310a3c60d0e9ecb8f35ef2641a89cabebaad8afb089eda`.
- `/api/console` and `/api/runtime/snapshot`: HTTP `401 access_required` without an invitation session.
- `matharc-research.service`: active after restart; systemd health and `readyz` post-start checks passed.

The workspace observatory and runtime API remain behind the same service and access boundary; only the public root dashboard path was restored.
