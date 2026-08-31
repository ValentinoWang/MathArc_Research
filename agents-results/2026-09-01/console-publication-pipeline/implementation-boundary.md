# Console Publication Pipeline: Implementation Boundary

- Request authority: repository owner requested the latest `console-dev-blueprint.html` be implemented and delivered through `main`.
- Frozen input: `docs/prototypes/console-dev-blueprint.html` and `docs/prototypes/problem-intel-console.html` at `31bb9704689548a69d0f020ec007af9688a6ad43`.
- Scope: M0 static export, M1 read-only observatory, M2 prototype review bridge to the existing sole write endpoint, M3 existing-source/topic read model, and M4 local isolated operations ledger.
- Non-goals: no external payment processor, identity provider, provider credentials, external literature search, mathematical-status inference, or extra research write endpoints. These need separate authority and runtime credentials.
- Isolation: operations must not import or mutate research replay state; console and observatory remain read-only except the existing review endpoint.
- Completion evidence: focused tests for each lane, full project suite and independent read-only reviews before `main` integration.
