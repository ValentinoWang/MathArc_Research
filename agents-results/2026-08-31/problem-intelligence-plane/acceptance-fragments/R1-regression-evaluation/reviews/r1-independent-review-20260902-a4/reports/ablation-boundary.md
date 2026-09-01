# R1 Independent Review: Ablation Boundary

- Lane: `ablation-boundary`
- Reviewer identity: `01a05c23-00d1-7161-b455-d8f789772122`
- Wrapper: `/Users/vsiyo/.codex/workers/run-l2.sh`
- Review mode: independent zero-write review; the only authorized write is this report
- Frozen source: `329b270460abf146561499fd5aa7ec4e62737eb1`
- Frozen input manifest SHA-256: `5bc1d1d6a02b2018e4956271dc20497e44a0ef779c0fbcafaf57d4f710add000`
- Authority boundary: this lane cannot accept R1 or alter R1/Q1/A5 state

## Findings

### P0

None.

### P1

1. **The approved contract's protected-test baseline does not match the frozen/current protected R1 test.** Contract v9 declares `tests/test_v02_regression_evaluation.py` SHA-256 `4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6`, while both the frozen manifest and HEAD contain `cfe0b0451b1a96a07eeb2d7e64fe6b80cff2498948373a740025e83978a6060f`. Git history confirms the contract-declared hash is the file at `8a6d908541b770461a081b43d8ced627befd0912`; commit `0cf567af98f8e32d4ddead6435ea2c49bbb272de` later changed the protected test's blocked-evidence/disposition assertions without updating the approved contract baseline. Freezing the changed bytes does not establish approval of the protected-test change. This violates the locked protected-test integrity requirement and blocks a PASS report even though the current focused suite is green.

## Frozen Input Integrity

All 10 paths in `frozen-inputs.json` match their declared SHA-256 values, and `git rev-parse HEAD` matches the frozen head. In particular, the evaluator is `667a89bf...77edd`, the fixture is `9b7fb5c0...c0429`, the contract is `c18a39ce...896f`, and the current R1 test is `cfe0b045...6060f`. The discrepancy above is between that internally consistent frozen campaign and the approved contract's protected-test table.

## Exact Commands And Results

```text
$ git rev-parse HEAD
329b270460abf146561499fd5aa7ec4e62737eb1

$ /usr/bin/shasum -a 256 agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260902-a4/frozen-inputs.json
5bc1d1d6a02b2018e4956271dc20497e44a0ef779c0fbcafaf57d4f710add000

$ jq -r '.inputs[] | [.sha256,.path] | @tsv' agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260902-a4/frozen-inputs.json | while IFS=$'\t' read -r expected path; do observed=$(/usr/bin/shasum -a 256 "$path" | /usr/bin/awk '{print $1}'); if [ "$expected" = "$observed" ]; then match_state=MATCH; else match_state=MISMATCH; fi; printf '%s\t%s\t%s\t%s\n' "$match_state" "$expected" "$observed" "$path"; done
MATCH for all 10 declared inputs; 0 mismatches.

$ env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/tmp /usr/bin/time -p python3 -m unittest tests.test_v02_regression_evaluation -v
Ran 7 tests in 0.019s
OK
real 0.24
user 0.13
sys 0.04
exit 0

$ env PYTHONDONTWRITEBYTECODE=1 python3 -c 'import json; from pathlib import Path; from matharc.v02.regression_evaluation import RegressionSuite; p=json.loads(Path("agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json").read_text()); s=RegressionSuite.from_dict(p); a=s.evaluate(); b=s.evaluate(); print(json.dumps({"digest":a.digest_sha256,"repeat_digest":b.digest_sha256,"equal":a==b,"cases":[{"case_id":c.case_id,"full_hit_ids":c.full_hit_ids,"outcomes":c.outcome_labels,"manual_minutes":c.manual_minutes,"routes":[{"route":r.route,"incremental_hits":r.incremental_hits,"leave_one_out_loss":r.leave_one_out_loss} for r in c.routes]} for c in a.cases]},sort_keys=True))'
digest=e6fdf4d1eb36b8179f6fcd6fd17e54b0a60332caa7a3d16115386fb85c52f13d
repeat_digest=e6fdf4d1eb36b8179f6fcd6fd17e54b0a60332caa7a3d16115386fb85c52f13d
equal=true
P-FRANKL-Q6: full=[frankl-boundary, frankl-structure], minutes=12.0, outcomes=[gap, hit, miss]
  FORWARD_CITATION increment/loss=[frankl-boundary]; ALIAS_AND_EQUIVALENCE=[]; STRUCTURAL_SEMANTIC=[frankl-structure]; REVIEW_AND_EXPERT_LEAD=[]
P-ARXIV-2601-22401-COLLISION: full=[erdos-397-alias, erdos-397-resolution, erdos-397-review], minutes=28.0, outcomes=[hit, miss]
  FORWARD_CITATION=[erdos-397-resolution]; ALIAS_AND_EQUIVALENCE=[erdos-397-alias]; STRUCTURAL_SEMANTIC=[]; REVIEW_AND_EXPERT_LEAD=[erdos-397-review]
P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS: full=[q6-residual-boundary], minutes=7.0, outcomes=[gap, miss]
  FORWARD_CITATION=[]; ALIAS_AND_EQUIVALENCE=[]; STRUCTURAL_SEMANTIC=[q6-residual-boundary]; REVIEW_AND_EXPERT_LEAD=[]
For every route, incremental_hits equals leave_one_out_loss on this fixture.

$ env PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import math
from matharc.v02.regression_evaluation import RegressionCase, RegressionValidationError

def check(label, minutes, outcomes=("hit",)):
    try:
        RegressionCase("P-FRANKL-Q6", "OPEN_REPORTED", minutes, outcomes, ())
    except RegressionValidationError as exc:
        print(f"{label}: REJECTED: {exc}")
    else:
        print(f"{label}: ACCEPTED")

for label, value in (("negative", -1), ("above-bound", 241), ("infinite", math.inf), ("nan", math.nan)):
    check(label, value)
check("illegal-outcome", 0, ("claim",))
PY
negative: REJECTED: manual_minutes must be finite and within the R1 bound
above-bound: REJECTED: manual_minutes must be finite and within the R1 bound
infinite: REJECTED: manual_minutes must be finite and within the R1 bound
nan: REJECTED: manual_minutes must be finite and within the R1 bound
illegal-outcome: REJECTED: expected_outcomes must be drawn from hit, miss, gap

$ rg -ni 'authorization|authorize|ResearchTrace|ClaimStatus|accuracy|precision|recall|statistic|confidence|p[-_ ]?value|production|device' matharc/v02/regression_evaluation.py agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json || true
<no matches>

$ git show 8a6d908541b770461a081b43d8ced627befd0912:tests/test_v02_regression_evaluation.py | /usr/bin/shasum -a 256
4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6

$ git show 0cf567af98f8e32d4ddead6435ea2c49bbb272de:tests/test_v02_regression_evaluation.py | /usr/bin/shasum -a 256
cfe0b0451b1a96a07eeb2d7e64fe6b80cff2498948373a740025e83978a6060f
```

## Ablation And Boundary Inspection

The evaluator constructs full coverage as the union of all four route hit sets. For each route it recomputes the union without that route, then derives both route increment and leave-one-route-out loss from set differences. Route order, three-case identity, unique normalized scopes/queries/sources, fixture content digest, and A4/T2 identity are validated before evaluation. Zero-increment routes remain explicit empty tuples. Outcomes are restricted to the closed `hit`/`miss`/`gap` set. Manual minutes are numeric, finite, non-boolean, and bounded inclusively to `0..240`.

The output schema contains only case identity, full hit IDs, outcome labels, manual minutes, route identity, increments, and leave-one-out loss. Static inspection found no authorization field, `ResearchTrace`, `ClaimStatus`, network/HTTP dependency, accuracy/precision/recall/statistical metric, confidence claim, production claim, or device claim.

## AC Disposition

| AC | Disposition | Evidence |
| --- | --- | --- |
| AC-01 | PASS for this lane | Three fixed cases, exactly four ordered independent route records per case; focused test green. |
| AC-02 | PASS for this lane | Repeat digest is identical; full coverage, route increments, leave-one-out loss, sorted outputs, and closed outcomes recompute deterministically. |
| AC-03 | PASS for this lane | Focused tamper tests pass; invalid minutes/outcome boundaries reject fail closed. |
| AC-04 | PASS for this lane | Passive in-memory result; forbidden authorization/trace/statistical/production/device terms and fields absent from evaluator and fixture. |
| AC-05 | FAIL | This required lane cannot issue PASS while the approved protected-test hash differs from the frozen/current test. |
| AC-06 | NOT ASSESSED | Identity-contract is a separate reviewer lane and is outside this lane's authority. |

No H-01 decision, R1 acceptance, Q1/A5 transition, publication decision, external-literature claim, statistical inference, production proof, device proof, or remote decision is made here.

## Residual Risk

The three-case fixture is intentionally too small and local to establish retrieval accuracy, recall, generalization, literature completeness, or production behavior. More immediately, the executable gate compares the current test hash to evidence/frozen-manifest metadata but does not reconcile it with the approved contract's protected-test table; therefore a post-approval protected-test change can remain internally self-consistent and green while bypassing the approved baseline. Repair requires an authorized contract/protected-baseline update or restoration of the approved test bytes, followed by a newly frozen independent review campaign.

Verdict: FAIL
