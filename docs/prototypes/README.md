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
