# Machine acceptance result: static

- Run ID: 20260903T180950Z-local-s1
- Task ID: FEAT-20260903-02
- Lane: machine/static
- Status: PASS
- Contract version: 1
- Source identity: landing-copy-candidate@1dbac14796b1fbbe98a04e5e8ef36c787d1e4fb13c1fbd9b7b62ea297dcbd444
- Runtime identity: local-python3.11
- Covers: AC-01

## Commands

```
python3 scripts/check_ui_copy_quality.py --evidence-dir agents-results/2026-09-03/console-landing-copy-harness/quality-gates
python3 scripts/check_console_visual_baseline.py
python3 scripts/check_blueprint_projection.py
```

## Observations

- ui-copy-quality: PASS (0 errors, 0 warnings) on 2 prototypes.
- console visual baseline: PASS (30 light / 26 dark tokens, 235 class names, 14 media rules unchanged by the landing redesign).
- blueprint projection: PASS.
- Known pre-existing failure, not part of this lane: `check_console_action_inventory.py` reports three access actions missing from SSOT §9.14 on `main` as well.
