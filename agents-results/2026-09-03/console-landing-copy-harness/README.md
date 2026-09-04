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

### Palette revision (second round, same day)

The owner reviewed the published prototype and asked for a stronger technical character. The
page moved from "academic paper" to **instrument console**, deliberately keeping STIX Two Text
for mathematical statements — a geometric sans would have read as a generic tech template and
would have thrown away the subject's own typesetting convention. The tech character comes from
the frame instead:

- neutrals re-cut from warm green to cool graphite (`--ground` `#F4F7F6` → `#E9EFF2`);
- accent given more chroma and a cyan lean (`#0F6B62` → `#00736B`; dark `#4FB3A5` → `#3BD6C4`);
- dark theme rebuilt as a deep blue-black housing (`#10191A` → `#060D10`);
- a hairline technical grid anchored to the top of the full-screen pages, masked out below;
- eyebrow labels moved to the monospace face, which the page already used for identifiers;
- corner radii tightened (11/10/9/8 px → 7/7/6/6 px).

Two accessibility defects surfaced and were fixed rather than carried forward: buttons on the
accent and gate colours had a hardcoded `#fff` that failed against the bright dark-theme accent,
and evidence badges `.ev2`/`.ev3` had hardcoded dark text that was dark-on-dark in the dark
theme. Both now use tokens that flip with the theme (`--on-e`, `--ink`).

**Contract handling.** The U1 static visual baseline pins the token table by SHA-256. The token
*names* (30 light / 26 dark), the three-mode structure, the 235 component class names and the 14
`@media` rules are all unchanged, so this is a values-only revision: `token_table_sha256` was
recomputed and re-pinned in `scripts/check_console_visual_baseline.py`, §9.13.1 of the view
contract was rewritten with the new values and a revision-6 note, the registered
wrong-fill-rule discriminant was recomputed, and the red fixture in
`tests/test_console_visual_baseline.py` was updated to the new accent literal. The frozen
`review-console.html` and `review_bundle.py` keep the old palette; that divergence is recorded
in `docs/prototypes/README.md` and needs a separate decision.

### Team-research section (third round, same day)

The owner asked whether four arXiv preprints by a team member could appear on the landing page,
and confirmed the author is on their team. They now appear as section 04, "我们自己在做的数学",
a two-by-two card grid of the four papers with an honest-disclosure band under it.

The section first shipped as team research with an explicit "MathArc does not claim to have
produced any of them" band, because that is what the repository records. On 2026-09-04 the owner
directed that it instead state the papers are results produced using MathArc, and that wording is
now live.

**This leaves an open contradiction that a human must close.** `docs/IMPROVEMENT_PLAN_V03.md`
still records arXiv:2607.28557 as a human-plus-conversation process that never entered the engine,
with the engine's only end-to-end run a toy odd-sum identity and the diagnosis "引擎与真实数学分离";
`V03_IMPLEMENTATION_STATUS.md` and `V03_REVIEW_TRACEABILITY.md` still record the R7 backfill of
that paper as not started; and the other three papers have no production record anywhere in the
repository. The landing page now asserts the opposite. This task did not resolve which side is
true, because the production facts belong to the owner and not to a frontend change. The
acceptance contract carries the conflict as a blocking item and AC-06 cannot pass until the owner
either updates those documents with a verifiable production record or withdraws the page's claim.
The band still states that all four are preprints and none is peer reviewed, which is
independently checkable on arXiv and was kept.

Two governance notes from this round: the contract's non-goal still said the U1 visual contract
was untouched, which the palette revision had made false, so it was corrected to name exactly what
stayed fixed (token names, class list, breakpoints) versus what changed (token values, re-pinned).
The browser gate's landing summary line hardcoded "4 anchors"; the section list is now a single
constant the loop and the summary both read, so the count cannot drift again.

The section adds no new component class names and no new `@media` rules, so the pinned class digest
and breakpoint map are unchanged; only page markup, the nav list, the motion controller's section
array and the gate's section constant moved.

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
