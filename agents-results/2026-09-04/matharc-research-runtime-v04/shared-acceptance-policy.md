# Shared acceptance policy: MathArc research runtime

# Shared acceptance policy: MathArc research runtime

All runtime contracts share the same evidence discipline for reliability,
protected test registration, and risk review. The shared policy never replaces
the node-specific acceptance seeds: every contract must name its own boundary,
test path, or failure condition. Harness is a governance-time compiler source,
not a product runtime dependency.

## Zero-tolerance invariants

The following values are release-blocking invariants and must be asserted by
protected tests or independent pilot evidence:

- Wrong mathematical promotion = 0.
- Duplicate execution, duplicate cost, and duplicate candidate import = 0.
- Cross-workspace writes = 0.
- A late result may not modify a closed generation = 0 violations.
- Public secret leakage = 0.
- Unauthorized runtime actions = 0.

Any violation keeps the node and its release below `ACCEPTED`, even when the
happy-path run succeeds. Acceptance owners must be independent from the
implementation owner for parallel scheduling, recovery, evidence conversion,
runtime action API, and adversarial pilot drills.
