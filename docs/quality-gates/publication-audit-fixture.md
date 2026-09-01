# Publication Audit Fixture Gate

`make publication-gate` runs `scripts/publication_audit_fixture.py` and is part of
the `quality` prerequisites for both `make ci` and `make ci-full`.

The runner creates a temporary workspace with `write_workspace_demo`, a minimal
LaTeX entrypoint containing the mapped `C-TARGET` claim, a matching claim map, an
abstract, and a serialized `PublicationBundle`. It then calls the real
`matharc.publication.gates.audit_publication` path. No LaTeX compiler, network,
formal solver, or other optional dependency is required.

## Contract

- Green proof: the generated technical-preflight fixture has no blocking errors.
- Red proof: `tests/test_publication_gates.py` changes the claim-map revision and
  requires the audit to fail closed.
- Scope: parser, workspace-integrity, claim-map, and abstract preflight wiring.
- Explicit non-scope: this fixture is synthetic and does not validate a real paper,
  theorem, novelty claim, peer review, human signoff, or publication authorization.

The optional JSON output defaults to `artifacts/ci/publication-audit-fixture.json`
and records `authorizes_real_publication: false` so the evidence boundary remains
machine-readable.
