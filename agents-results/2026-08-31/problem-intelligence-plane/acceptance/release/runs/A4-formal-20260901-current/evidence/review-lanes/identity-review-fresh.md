# A4 Fresh Identity and Boundary Review

- Run: `A4-formal-20260901-current`
- Lane: `identity-review-fresh`
- Review mode: read-only; no SSOT state, acceptance record, or source edits
- Requested baseline: `main@3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`
- Requested contract v2 SHA-256: `4b7ac7ea035d59be7c87fef9867b97529f8b00f68c207d7460963cd625095c84`
- Requested binding SHA-256: `7b299dff38c8c36b9041c8f121b28dc0b70a6539c894081bd4111dab17b4cc78`
- Requested checklist SHA-256: `cd57b8e24177664d0796084d81cda6891703a9fe7a6b5a958dbd943cfc180593`

## Identity Readback

`git rev-parse HEAD` and `git ls-remote origin refs/heads/main` both resolve to
`3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`. The protected implementation and
test bytes at this checkout match the current-HEAD hashes recorded by the
archive and regression lanes:

| Path | SHA-256 |
| --- | --- |
| `matharc/v02/topic_observation.py` | `16743b6097480044253c50fc8188b65a23062e5f57435361863311b1483a80e1` |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` |
| `tests/test_v02_topic_observation.py` | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` |

The requested contract, binding, and checklist hashes match the current working
files exactly. However, `git show HEAD:<path>` yields the prior hashes
`b0f3211501529a5a1f3d327ebaba49aa09dc7013c9c1a5a0b3d2a01c89e1e28f`,
`e55edb8dbb1413d5a83fd500a3f466d68f87832196408c3acfa6f46f8ad2ee52`, and
`bdaee164e73c19e1a6fd977818157200fd04414bb2a4b8f6c9cd172e7fbf7e3e`.
The three v2 files are therefore uncommitted identity inputs, not artifacts of
`main@3353d6a`. The worktree also contains those three modifications and the
current human/release run directories as untracked content.

## Scope and Boundary

The v2 contract scope is limited to the offline, source-fixed three-archive
topic-observation engineering loop: replay, recovery, deduplication, budget,
manual-queue failure modes, and non-promotion. Its explicit non-goals exclude
mathematical proof, live external-literature confirmation, production/device
evidence, and public-release authorization. The T2 fixture, `E-T2-A4` hard edge,
and current-run archive/regression returns preserve this boundary. No boundary
overclaim was found in those lane reports.

The A4 SSOT node remains `execution_state: VERIFIED`, while `E-A4-R1` requires
`ACCEPTED`; this review does not alter that state. The current human run
`20260901T141500Z-local-a4f002` has H-01 `ACCEPTED` under the requested v2
hashes, but its snapshots are also uncommitted.

## Evidence Identity Gap

`evidence/A4.json` is still `EV-A4-ACCEPTED-2` and points to the historical
formal run `A4-formal-20260901-0808`, human run `20260901T081500Z-local-a4f001`,
and source identity `5af1d9ff6fde02d86633cca50cf815ef04661d4a`. Its stored
`acceptance_self_check`/`proposed_state` are `pass`/`ACCEPTED`, which do not
match the current `3353d6a` + contract-v2 run inputs. Existing current-run
archive and regression reports are useful lane evidence, but they do not repair
the stale A4 evidence record or make the dirty contract files part of `main`.

Consequently AC-05 (current main, contract, edge, T2 evidence, and three return
hash agreement) is not proven, and the current formal acceptance identity cannot
be considered closed. This is an identity/readiness failure, not a finding that
the bounded archive implementation or its non-claim boundary is unsound.

## Verdict

`proposed_state: FAILED`

The lane is failed because the supplied v2 contract/binding/checklist and human
run are uncommitted while `evidence/A4.json` still asserts an older accepted
identity. Commit or otherwise durably bind the v2 tuple to the target `main`
commit, regenerate `evidence/A4.json` and a serial current release result, then
re-run the required synthesis. This lane has no authority to accept A4, update
SSOT state, unlock R1, or authorize publication.
