---
name: matharc-publication
description: Run MathArc's fail-closed publication audit against a sealed workspace, review bundles, and LaTeX claim map.
---

# MathArc Publication

This skill is a thin invocation layer. Scientific truth and hard gates live in
`matharc.publication` and `matharc.v02`; do not infer readiness from prose or
from recursively scanning arbitrary JSON.

Run:

```bash
python -m matharc.publication audit \
  --workspace <workspace> \
  --publication-bundle <publication-bundle.json> \
  --latex <source/main.tex> \
  --claim-map <source/claim-map.json> \
  --abstract <source/abstract.txt> \
  --compile
```

Exit code 0 means machine gates passed. A non-zero exit is a blocker. Human
sign-off, novelty, authorship, license, and submission-route decisions remain
explicit human gates and must not be synthesized by this skill.
