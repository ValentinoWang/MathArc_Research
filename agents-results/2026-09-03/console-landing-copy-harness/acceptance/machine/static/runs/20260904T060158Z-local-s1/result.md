# Machine acceptance result: static

- Run ID: 20260904T060158Z-local-s1
- Task ID: FEAT-20260903-02
- Lane: machine/static
- Status: PASS
- Contract version: 1
- Source identity: landing-copy-candidate@9f2e53baa841330aaf6959136cc35020493b00e4d00f4eaef3612a4e96cd3feb
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
