# Console visual baseline

This directory currently contains a planning contract, not runtime visual
evidence. `manifest.json` is deliberately `planned` and `inactive`; all capture,
screenshot, run, browser, timestamp, digest, and human-review records remain
empty or null until U1 is activated and an actual capture run occurs.

The planned baseline is one PNG for each of 32 unique views at each of eight
viewports: six desktop widths and two mobile sizes. The expected inventory is
therefore 256 captures. The separate browser regression inventory contains 52
cases (32 base cases plus 20 state/action variants); it does not create 52
unique views, prove 52 real interactions, or change the 256-image baseline.

## Activation and population

Before this manifest can represent captured evidence:

1. Activate U1 through the approved SSOT route and resolve ownership of the
   `landing` and `login` views.
2. Materialize the pinned HTML bytes from commit
   `31bb9704689548a69d0f020ec007af9688a6ad43` and verify their SHA-256 before
   capture.
3. Produce all 256 PNGs and populate a distinct record for every view/viewport
   pair. Each record must include source, browser, viewport, state or fixture,
   tool, run, and capture-time provenance.
4. Hash every PNG and the separate DOM-structure and computed-style records.
   DOM evidence must cover `.card`, `.grid2`, `.chain`, and `.li`; style evidence
   must include font families, resolved color tokens, and `.card` radius and
   border values.
5. Compute `consumer_surface_digest` from the canonical consumed contract, then
   execute the applicable A6 and A7 H-01 reviews as independent human evidence.

After activation, completed records are immutable. A changed source identity,
view inventory, viewport, DOM/style requirement, browser, tool, state, or
fixture invalidates affected evidence and requires a new capture identity.
Filename reuse never preserves validity. Captures remain project-owned with
release retention; they do not become Harness or production evidence.
