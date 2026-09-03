# Machine acceptance result: e2e

- Run ID: 20260903T174943Z-local-e1
- Task ID: FEAT-20260903-02
- Lane: machine/e2e
- Status: PASS
- Contract version: 1
- Source identity: landing-copy-candidate@7cd12399cd57a2bcca66a3ffc9532defdf95d6d11602bdb2c5ee07415b919a2b
- Runtime identity: local-playwright-fixture (chromium, font_mode=fallback-local)
- Covers: AC-02, AC-03

## Command

```
MATHARC_GATE_EVIDENCE_DIR=agents-results/2026-09-03/console-landing-copy-harness/evidence \
MATHARC_GATE_FONT_MODE=fallback-local node scripts/console_browser_gate.mjs
```

## Observations

```
access workflow passed: protected boundary, pending application, invalid/valid invite, Cookie restoration, replay rejection, logout, guest demo; 10 hash-bound screenshots
landing scroll experience passed: sticky nav state, 4 anchors, reveal completion, single-line controls, reduced-motion visibility; 5 hash-bound screenshots (font mode fallback-local)
console browser gate passed: 52 cases x 2 campaigns x 6 widths
mobile viewport checks passed: mobile-390=390x844, mobile-820=820x1180
keyboard checks passed: tabindex disclosures activated with Enter and Space
M1 SSE workflow: emitted event 4, refreshed /api/console, and reconnected with after=4
M2 review workflow: exercised real queue, bundle, rendered rejection, token clearing, and persisted approval
```

- Landing manifest: 5 hash-bound captures, font_mode=fallback-local; review_result PASS means the scroll-experience assertions held (see `review_note`).
- Access manifest: 10 hash-bound captures with the rewritten access messages.
- Fallback-local fonts: metrics are from installed system CJK fonts because this machine cannot reach the font CDN; a webfont-loaded machine should re-run before human review of typography.
