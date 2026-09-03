# Guard Card: landing-scroll-experience

- Failure class: a long-scroll surface accepted without runtime proof of its scroll behaviour and inline-control layout, or a screenshot manifest whose PASS was written without assertions
- Scope: the `landing` view of `docs/prototypes/problem-intel-console.html` at 1440×900 (light and dark), 390×844 (touch) and a 1240×900 reduced-motion context
- Blocking level: blocking in `node scripts/console_browser_gate.mjs` (`testLandingScrollExperience`)
- Evidence: `landing-screenshot-manifest.json` plus five hash-bound captures under the task evidence directory (`MATHARC_GATE_EVIDENCE_DIR`), each recording `font_mode`
- Fast proof: none (runtime only); the static baseline still pins tokens, class names and breakpoints
- Repair path: keep the landing CSS inside the frozen U1 static contract (no new tokens, class names or `@media` rules), keep `scroll-margin-top` on sections, `white-space:nowrap` on nav labels and hide the section links under 820 px, keep reveal attributes script-applied so reduced-motion readers and script failures see everything
- Retirement condition: fold into a schema-validated scroll-experience lane of `runtime-visual-verification` once it exists
- Upstream: `Core/harnesses/scroll-surface-layout-guard-card.md` in Harness Engineering

## Failure Contract

The gate fails when the nav is not sticky, `data-scrolled` does not flip, an anchor lands outside `[nav bottom − 2px, nav bottom + 40px]`, more than one or no nav link carries `aria-current` after an anchor click, any revealed element in view stays below opacity 1, any single-line control (nav labels, header buttons, hero buttons and pills) exceeds 1.9 line-heights, the 390 px page overflows horizontally or still shows the desktop section links, or a reduced-motion context receives reveal attributes or transparent content.

## Evidence

- Red proof: `agents-results/2026-09-03/research-preview-access/mobile-logged-out.png` (nav labels wrapped vertically while the manifest said PASS); synthetic: remove `white-space:nowrap` from `.lpnav .links button` or `scroll-margin-top` from `.sec` and the corresponding assertion fails.
- Green proof: the 2026-09-03 gate run in `agents-results/2026-09-03/console-landing-copy-harness/evidence/`.

## Calibration

Screenshots prove rendered layout at the declared font mode only. Hierarchy and wording remain a human review recorded in the task acceptance checklist; the manifest's `review_note` says so.
