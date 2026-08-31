# A5 Final Static Verification

The selected final static run executes the strengthened source-level A5 guard. It rechecks the Q1 evidence, policy fixture bytes/digest, implementation/test identity, structured evidence schema, selected run identity, source-only scope and the required post-push ref readback.

Required commands: focused A5/Q1/R1 tests, `test_v02*.py` discovery, full discovery, `git diff --check`, contract validation and split-root evidence check. All commands passed in the final release synthesis.
