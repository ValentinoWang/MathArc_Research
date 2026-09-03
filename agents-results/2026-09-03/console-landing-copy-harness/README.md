# Console landing, copy and Harness feedback (2026-09-03)

Task ID: `FEAT-20260903-02`. Branch: `claude/frontend-visual-copy-harness-q4iini`.

Scope requested by the project owner: (1) raise the landing page's visual impact and design its
scroll experience; (2) check every user-visible sentence across the site for meaning, clarity and
naturalness; (3) do not stop at fixing this page — turn the causes into Harness rules, checks and
routes so the next generation or modification avoids the same classes of defect; (4) find the
earlier HTML demo and align demo and production.

## What the demo and the production page are

`docs/prototypes/problem-intel-console.html` is both: the workspace server serves it as the console
dashboard (`--dashboard`) and it opens standalone with demo data. The earlier HTML demo,
`docs/prototypes/review-console.html`, is the frozen v3 recruiting mockup whose design tokens the
backend `render_review_bundle_html` reuses. Alignment therefore meant three things: one source file for
demo and served console; the same vocabulary in the prototype and in the backend labels
(`review_server.py`, `review_bundle.py` now say 机器判定即可 / 需一名评审人判断 / 需两名独立评审人分别判断,
as does the roster view); and the frozen demo re-inventoried against the same copy lexicon (it passes
unchanged, so it was not restyled — the freeze in `docs/DEV_PATH_V03.md` §5 still holds).

## Findings

### Landing (首页)

- Hero had one primary focus but no evidence object: statement, paragraph, two buttons, then a legend.
  Nothing showed what "a problem going through three steps" looks like. It now carries a demo figure
  with the three real demo states (7/9 checks, root claim pending after 7 rounds, result absorbed by
  prior work, disclosure level 2/4), an eyebrow naming the audience, a larger statement and a two-column
  hero that stacks on phones.
- Sections had no shared rhythm (heading → lead → content, varying spacing) and the page did not react
  to scrolling at all: static nav, anchors hidden under nothing, no reveal, no current-section state.
  Each section now has the same eyebrow → heading → lead → content rhythm, a numbered eyebrow that
  matches the nav labels, and the nav is sticky with a current-section underline; anchors land below
  the nav; content reveals on entering the viewport with a short stagger; readers who prefer reduced
  motion get everything visible with no attributes at all; a closing band with two paths ends the page.
- On the 390 px capture every nav label had wrapped into a vertical column of characters. The evidence
  manifest still said PASS. Nav labels are now `nowrap` and hidden under 820 px.
- All styling stays inside the frozen U1 static contract (§9.13 of the view contract): no new tokens,
  no new class names, no new `@media` rules. New behaviour is expressed through attribute selectors
  (`data-scrolled`, `data-reveal`, `aria-current`) and IDs, so `check_console_visual_baseline.py` stays
  green without an SSOT revision. The `landing` row of §9.15 remains `已推迟`: the view still reads no data.

### Copy (全站)

The inventory covered 2 906 CJK segments. Most copy is deliberate and specific; the defects were
concentrated in three places: developer vocabulary in access and live-view messages (`服务端确认会话`,
`已接线`, `读模型`, `同源`), machine tokens rendered as prose in the fallback and local-projection states
(`not_configured`, `PASSED`, `UNCALIBRATED`, `event_sequence`, `campaign report`), and a few landing
sentences that chained undefined terms or used literal translations (`杀手测试`). Two adjacent topbar
labels both read `演示数据` for different facts. Every rewrite with its reason is in `copy-review.md`.

## Root causes, and where each one now lives in the Harness

| Symptom | Why it happened | Harness change |
| --- | --- | --- |
| Generated-sounding or opaque sentences reached the page | Copy was written inline while rendering; no inventory, no per-string question (object / fact / next step / whose words), reviewed only through screenshots that hide fallback states | `Core/skills/ui-copy-quality` (checker + review checklist + red/green fixtures); `product-frontend-harness.md` "Copy Quality Route"; guard card `ui-copy-quality-guard-card.md` |
| Machine identifiers and English tokens leaked in fallbacks | Gates asserted text existed and numbers derived from data, never that text meant something | Same checker (six stable classes) plus the runtime `scanCopyQuality` pattern for browser gates |
| Demo and backend disagreed on the same enum labels | No "one name per concept across surfaces" rule | Checklist consistency pass; route step 4 |
| Visual hierarchy was flat | Screen contracts describe fields and regions; nobody owned rhythm or a hero evidence object | `product-frontend-harness.md` "Long-Scroll Surfaces" |
| Scroll behaviour was never designed | Scroll was not a requirement of the contract, so it was not built or measured | Same section; runtime-visual-verification gains a scroll-experience walk; guard card `scroll-surface-layout-guard-card.md` |
| Mobile nav wrap shipped with a PASS manifest | The capture script wrote `review_result: PASS` unconditionally | Manifests must say what PASS means (`review_note`) and record `font_mode`; `quality-ai-harness.md` anti-patterns |
| Evidence captured with whatever fonts the network gave | Font mode was documented in the SSOT but never recorded or controlled | Gate `MATHARC_GATE_FONT_MODE`; manifest `font_mode` |

## Project-level changes

- `docs/prototypes/problem-intel-console.html`: landing redesign, `LandingMotion` controller, copy fixes,
  topbar source label (`未接入工作区`), login hints, live-view fallbacks.
- `matharc/v02/review_server.py`, `matharc/v02/review_bundle.py`: assurance labels aligned with the prototype.
- `scripts/check_ui_copy_quality.py` + `docs/quality-gates/ui-copy-lexicon.json` + `tests/test_ui_copy_quality.py`
  (blocking in `make quality` via `console-copy-gate`).
- `scripts/console_browser_gate.mjs`: `testLandingScrollExperience`, `scanCopyQuality`,
  `assertSingleLineControls`, `MATHARC_GATE_EVIDENCE_DIR`, `MATHARC_GATE_FONT_MODE`, manifest `font_mode`/`review_note`.
- `.harness/guards/ui-copy-quality.md`, `.harness/guards/landing-scroll-experience.md`,
  `.harness/overlays/project-harness-adapter.yaml`, `Makefile`, `docs/prototypes/README.md`.

## Evidence in this directory

- `copy-review.md` — meaning pass (before / after / reason).
- `quality-gates/ui-copy-quality.{json,md}` — lexical gate result.
- `evidence/` — browser gate captures and manifests (`screenshot-manifest.json` for the access flow,
  `landing-screenshot-manifest.json` for the landing walk), both recording `font_mode: fallback-local`
  because this machine cannot reach the font CDN; metrics may differ from a webfont-loaded machine.
- `acceptance-contract.md`, `acceptance/` — machine acceptance record; human acceptance stays in
  `acceptance/human/2026-W36/未-2026-09-03-FEAT-20260903-02/` and is not signed.

## Known gaps left open

- `scripts/check_console_action_inventory.py` fails on `main` before this change (`access-mode`,
  `application-submit`, `logout` are emitted but absent from SSOT §9.14). It is not part of `make ci`
  and needs an SSOT revision; left untouched and reported.
- The static baseline still pins 235 class names; any future landing change that needs a new class must
  revise §9.13 with the snapshot procedure rather than edit the digest.
- Hierarchy and wording remain a human judgement; the machine PASS covers layout and lexical facts only.
