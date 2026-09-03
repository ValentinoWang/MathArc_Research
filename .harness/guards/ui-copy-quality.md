# Guard Card: ui-copy-quality

- Failure class: user-facing copy that leaks machine identifiers, rendering leftovers, filler phrases, implementation jargon, glued CJK/ASCII, or doubled words
- Scope: `docs/prototypes/problem-intel-console.html` (served as the console dashboard) and `docs/prototypes/review-console.html`; text between tags, JavaScript string literals containing CJK, placeholder/title/aria-label attributes; identifier containers (`code`, `.mono`, `.hash`, `.ev`, `.seq`) and lexicon exceptions excluded
- Blocking level: blocking in `make ci` / `make ci-full` (fast static gate)
- Lexicon: `docs/quality-gates/ui-copy-lexicon.json` (project-owned; edit it with a reason, never the checker)
- Fast proof: `python3 scripts/check_ui_copy_quality.py` and `python3 -m unittest tests.test_ui_copy_quality`
- Runtime proof: `scanCopyQuality` in `scripts/console_browser_gate.mjs` (text nodes outside identifier containers, every view × campaign × viewport)
- Repair path: rewrite for a reader who sees only the screen (`source fact → reader question → concrete copy → next action`); record before/after/reason in the task `copy-review.md`; keep one name per concept across the prototype, backend labels (`review_server.py`, `review_bundle.py`) and blueprint
- Retirement condition: replace only when copy is generated from a reviewed string table with its own leak checks and the fixtures migrate
- Upstream: `Core/skills/ui-copy-quality` and `Core/harnesses/ui-copy-quality-guard-card.md` in Harness Engineering (promoted from this project on 2026-09-03)

## Failure Contract

The guard fails when any inspected segment contains `undefined`/`NaN`/`TODO`-class leftovers, a snake_case or SCREAMING_CASE identifier (or an all-caps word of six or more letters embedded in a CJK sentence) outside a declared identifier container and not allowlisted, a lexicon filler phrase, a lexicon jargon term without an allowed context, or a CJK character glued to an ASCII letter or digit. A repeated two- or three-character CJK word is a warning unless allowlisted as reduplication.

## Evidence

- Red proof: `tests/test_ui_copy_quality.py` synthetic segments for every class; historical case `docs/prototypes/problem-intel-console.html` at `530de20` reported `服务端` ×2 and a filler hit on first run, and the 2026-09-03 manual review found `not_configured`, `PASSED`, `UNCALIBRATED`, `event_sequence`, `campaign report`, `杀手测试`, `每次每次` and duplicate topbar labels that the previous gates had passed.
- Green proof: identifiers inside `.mono`/`<code>`, allowlisted field names (`reviewer_id`), spaced CJK/ASCII, legitimate reduplication (`一步一步`), comments and CSS ignored, line numbers stable across stripped comments.

## Calibration

The checker is lexical and proves the absence of mechanical defects only. Whether a sentence is clear is decided in the meaning pass recorded in `copy-review.md`, not by this guard. The frozen `review-console.html` passes unchanged.
