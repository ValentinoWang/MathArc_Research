# A5 Static Verification Summary

- Source identity: `9d727862a5566b32fdeec3af017dc466a5f9dd12+a5-release-candidate`
- Runtime: Python 3.13 local test environment
- Scope: hash-bound A5 source-level record and Q1 disclosure boundary

| Command | Result |
| --- | --- |
| `python3.13 -m unittest -v tests.test_v02_release_decision tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation` | PASS |
| `python3.13 -m unittest discover -s tests -p 'test_v02*.py'` | PASS |
| `python3.13 -m unittest discover -s tests` | PASS |
| `git diff --check` | PASS |

The unit test binds Q1 evidence, policy digest, implementation and protected-test identity; it also rejects schema or scope expansion and requires all selected A5 run results to be `PASS`. This is source-level evidence only.
