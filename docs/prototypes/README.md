# Prototypes

## `review-console.html`

Status: **`FROZEN_RECRUITING_DEMO`** — the current v3 recruiting/demo
prototype. It is a self-contained HTML mockup: some evidence rows are
illustrative rather than replayable against the live gates.

No further visual/product iteration is funded until the conditions in
[`../DEV_PATH_V03.md`](../DEV_PATH_V03.md#5-prototype-freeze) (§5, "Prototype
freeze") all hold. Recruiting may use the frozen prototype as-is, but
prototype behavior is not evidence that the backend contract exists.

`matharc/v02/review_bundle.py`'s `render_review_bundle_html` reuses this
file's CSS/design tokens — do not restyle it without checking that consumer.

## `problem-intel-console.html`

The console prototype is also the page the workspace server serves as the dashboard
(`--dashboard`), so the demo and the served console are one source file. Its landing view
is a scroll surface guarded at runtime by `testLandingScrollExperience` in
`scripts/console_browser_gate.mjs`; its copy is guarded by `scripts/check_ui_copy_quality.py`
with the lexicon in `docs/quality-gates/ui-copy-lexicon.json`. Landing styling stays inside the
frozen U1 static contract (no new tokens, class names or `@media` rules): new behaviour is
expressed through attribute selectors (`data-scrolled`, `data-reveal`, `aria-current`) and IDs.

### Palette divergence from the frozen review console (2026-09-03)

`problem-intel-console.html` moved to a cooler "instrument console" palette (revision 6 of
§9.13.1 in the U1 view contract): cool-graphite neutrals, a cyan-leaning teal accent, and a
deeper blue-black dark theme. `review-console.html` is `FROZEN_RECRUITING_DEMO` and a palette
change is not one of its allowed unfreeze exceptions (security, privacy, accessibility only),
so it keeps the original warm-green palette, and so does `render_review_bundle_html` in
`matharc/v02/review_bundle.py`, which instantiates the frozen tokens.

The two therefore no longer share one palette. This is a recorded, deliberate divergence, not
drift: aligning the review console and the review-bundle renderer needs the freeze conditions
in [`../DEV_PATH_V03.md`](../DEV_PATH_V03.md#5-prototype-freeze) to hold, or an explicit
project decision to lift the freeze for this purpose. Until then, do not "fix" either side to
match the other. Token *names* remain identical across all three, so the alignment, when it is
funded, is a values-only change.

