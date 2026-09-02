# Memory

## `research_episodes_v02.jsonl` — active

Loaded by `EpisodeMemory.load_jsonl()` and consumed by
`matharc/v02/research_director.py`'s `AdaptiveResearchDirector` to steer
live v0.2 research campaigns away from previously-observed failure modes.

## `research_lessons_v02.json` — seed data, not yet wired into code

A curated catalog of generic proof-failure patterns (`failure_class` ->
`trigger_pattern` / `kill_test` / `repair` / `examples`), sharing the same
`failure_class` taxonomy as the episodes above. **No code currently loads
this file** — confirmed by a repo-wide search for `research_lessons_v02`
outside this note. It sits here as authored reference material, not a
live input to any campaign, director, or test.

Do not assume it's consulted at runtime just because it lives next to the
file that is. If you want to actually use it (e.g. have
`AdaptiveResearchDirector` look up the matching `kill_test`/`repair` for an
observed `failure_class`), that's a real feature addition — load and wire
it deliberately rather than assuming the schema similarity means it's
already connected.
