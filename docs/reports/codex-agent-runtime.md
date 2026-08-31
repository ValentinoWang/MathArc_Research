# Codex Agent Runtime for MathArc Research

Status: frozen for MathArc Research v0.1

## Purpose

The Web console now delegates interactive research turns to the official Codex CLI instead of simulating agent replies in browser JavaScript. Codex is a worker behind MathArc's verifier boundary:

```text
browser request
  -> frozen theorem state + selected worker charter
  -> codex exec --json --output-schema ...
  -> public reasoning summaries / commands / file changes / MCP calls
  -> structured final proposal
  -> append-only session ledger
  -> MathArc evidence and promotion gates
```

Codex is not an acceptance authority. A response may propose a claim, refute a route, or request tools, but it cannot assign `VERIFIED` or widen mathematical scope.

## Official CLI surface used

The adapter uses the non-interactive CLI contract implemented by `openai/codex`:

```bash
codex exec \
  --json \
  --skip-git-repo-check \
  --sandbox read-only \
  --cd /workspace \
  --output-schema /tmp/matharc-agent.schema.json \
  --output-last-message /tmp/matharc-last-message.json \
  --config 'approval_policy="never"' \
  --config 'sandbox_workspace_write.network_access=false' \
  --config 'web_search="disabled"' \
  -
```

A subsequent turn can resume the returned thread:

```bash
codex exec [global options] resume <thread_id> -
```

The JSONL event stream contains thread lifecycle events and typed items such as:

- public reasoning summary;
- agent message;
- command execution;
- workspace file change;
- MCP tool call;
- web search;
- to-do plan;
- errors and token usage.

References:

- <https://github.com/openai/codex>
- <https://github.com/openai/codex/blob/main/codex-rs/exec/src/cli.rs>
- <https://github.com/openai/codex/blob/main/sdk/typescript/src/events.ts>
- <https://github.com/openai/codex/blob/main/sdk/typescript/src/items.ts>

## Worker roles

The browser exposes five stable workers:

| role | responsibility | default failure test |
|---|---|---|
| `strategist` | isolate the next load-bearing obligation and diversify mechanisms | verify routes differ by object, invariant, operation, representation, and missing obligation |
| `prover` | construct one atomic lemma, certificate, or reduction | try small, degenerate, extremal, and boundary instances before promotion |
| `falsifier` | attack scope, quantifiers, assumptions, and candidate bridges | produce the smallest exact counterexample or explicit missing hypothesis |
| `verifier` | design statement correspondence, checkers, hashes, replay, and independent reconstruction | compare generator and checker implementation families |
| `synthesizer` | state the strongest verified result and every unresolved critical obligation | keep full theorem closure binary and recheck the claim boundary |

## Structured final response

Codex receives a JSON Schema. Its final response must contain:

```json
{
  "status": "progress | blocked | falsified | candidate | error",
  "executive_summary": "...",
  "public_reasoning": {
    "objective": "...",
    "premises": ["..."],
    "proposed_move": "...",
    "observation": "...",
    "falsification": "...",
    "decision": "..."
  },
  "claim_updates": [
    {
      "claim_id": "C-...",
      "action": "propose | refine | block | refute | keep_open",
      "statement": "...",
      "scope": "...",
      "evidence_needed": ["..."]
    }
  ],
  "tool_requests": [
    {
      "tool": "...",
      "purpose": "...",
      "command": "...",
      "expected_discriminator": "..."
    }
  ],
  "risks": ["..."],
  "next_actions": ["..."],
  "claim_boundary": "..."
}
```

`verified` and `accepted` are deliberately absent from the allowed status values.

## Security and trust boundary

1. The default browser mode is `read-only`.
2. `workspace-write` requires an explicit UI action for every selected mode.
3. The Web API accepts only `read-only` and `workspace-write`; it never exposes Codex's dangerous bypass flag.
4. Network and Web search are disabled by default.
5. The browser cannot select an arbitrary server-side working directory.
6. Request bodies are capped at 64 KiB.
7. Provider credentials are inherited by the process but never serialized into the public session ledger.
8. Temporary output-schema and last-message paths are redacted from the displayed command.
9. Session outputs are stored under `.matharc/codex-sessions/` with a deterministic result digest.
10. Public `reasoning` items are treated as summaries, never as a substitute for proof artifacts.

## API

Read-only endpoints:

```text
GET /api/agent/status
GET /api/agent/roles
GET /api/agent/sessions
GET /api/agent/sessions/<local_session_id>
```

Execution endpoints:

```text
POST /api/agent/turn
POST /api/agent/stream
```

`/api/agent/stream` uses Server-Sent Events and flushes every normalized Codex event immediately.

## Configuration

```bash
export CODEX_API_KEY=...
export MATHARC_CODEX_MODEL=...
export MATHARC_CODEX_WORKSPACE=/path/to/Harness_Engineering
export MATHARC_CODEX_SANDBOX=read-only
export MATHARC_CODEX_TIMEOUT=900
export MATHARC_CODEX_NETWORK=0
export MATHARC_CODEX_WEB_SEARCH=disabled
```

The Docker image installs `@openai/codex`; credentials remain runtime-only.

## CLI

```bash
python -m matharc codex status --workspace .

python -m matharc codex turn \
  --run artifacts/demo/run.json \
  --role falsifier \
  --message 'Audit the current global bridge.' \
  --sandbox read-only \
  --workspace .

python -m matharc codex sessions \
  --run artifacts/demo/run.json \
  --workspace .
```

## Lessons incorporated from the Frankl q=6 closure

The Codex prompt and UI now encode the following rules learned during the proof program:

- a compressed state-space calculation must be checked against an uncompressed exhaustive audit before closure;
- a special-case theorem and the global conjecture must appear as separate binary states;
- byte-identical cold replay is a release artifact, not a prose assurance;
- checker independence and claim correspondence are visible in the evidence view;
- a discovered exceptional type is preserved as a regression object instead of being hidden by a stronger aggregate bound;
- Agent output is a proposal until the exact verifier and dependency DAG accept it.
