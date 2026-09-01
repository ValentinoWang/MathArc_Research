PYTHON ?= python3
PIP := $(PYTHON) -m pip
export PYTHONPATH := $(CURDIR)$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: bootstrap bootstrap-full ci-preflight formal-preflight test test-full typecheck architecture workflow-policy publication-gate quality demo validate serve codex-status acceptance v02-demo v02-validate v02-acceptance frankl-replay console-browser-gate ci ci-full clean-ci baseline smoke-claude

bootstrap:
	$(PIP) install -e ".[research,dev]"

bootstrap-full:
	$(PIP) install -e ".[research,dev,formal]"

ci-preflight:
	$(PYTHON) scripts/ci_preflight.py

formal-preflight:
	$(PYTHON) scripts/ci_preflight.py --require-formal

test:
	$(PYTHON) scripts/run_unittest_suite.py --summary-path artifacts/ci/unittest-summary.json

test-full:
	$(PYTHON) scripts/run_unittest_suite.py --require-z3 --summary-path artifacts/ci/unittest-summary.json

typecheck:
	$(PYTHON) -m mypy --strict matharc/v02 matharc/publication

architecture:
	$(PYTHON) -m unittest -v tests.test_claim_architecture tests.test_v02_research_director

workflow-policy:
	$(PYTHON) scripts/check_matharc_workflows.py

publication-gate:
	$(PYTHON) scripts/publication_audit_fixture.py

quality: typecheck architecture workflow-policy publication-gate

demo:
	$(PYTHON) -m matharc demo --out-dir artifacts/demo

validate: demo
	$(PYTHON) -m matharc validate --run artifacts/demo/run.json

v02-demo:
	$(PYTHON) -m matharc.v02 demo --out-dir artifacts/v02-demo

v02-validate: v02-demo
	$(PYTHON) -m matharc.v02 validate --trace artifacts/v02-demo/research-trace.json

codex-status:
	$(PYTHON) -m matharc codex status --workspace .

serve: demo
	$(PYTHON) -m matharc serve --run artifacts/demo/run.json --workspace . --port 8000

acceptance:
	$(PYTHON) scripts/v0_1_acceptance.py

v02-acceptance:
	$(PYTHON) scripts/v0_2_acceptance.py

frankl-replay:
	$(PYTHON) examples/frankl_q6_two_small.py --output artifacts/frankl-q6-two-small-python.json
	$(PYTHON) -c "import json; assert json.load(open('artifacts/frankl-q6-two-small-python.json')) == json.load(open('benchmarks/certificates/frankl-q6-two-small-python.json'))"

# Browser regression gate for the prototype contract in console-dev-blueprint.html.
# It requires the repository's existing Node.js plus a locally installed or global
# Playwright module with Chromium. Missing browser capability is a hard failure.
console-browser-gate:
	node scripts/console_browser_gate.mjs

# Fast/developer gate. It always prints the exact skip count and formal-capability
# state, but an environment without z3 is DEGRADED and must not be cited as the
# authoritative green Gate 0 result.
ci: ci-preflight quality test validate v02-validate codex-status acceptance v02-acceptance frankl-replay console-browser-gate
	@echo "Gate 0 developer CI complete. For authoritative green evidence run: make ci-full"

# Authoritative local Gate 0-b gate: formal extra must exist and SMT tests must
# actually run rather than all being skipped.
ci-full: formal-preflight quality test-full validate v02-validate codex-status acceptance v02-acceptance frankl-replay console-browser-gate
	@echo "Gate 0 authoritative CI complete: formal capability present and SMT suite executed."

# Reproducibility proof: archive the committed project and its root registry
# authority, bootstrap a fresh venv with formal extras, and run ci-full there.
clean-ci:
	$(PYTHON) scripts/clean_checkout_ci.py

# Produce a dated G0-c record only after ci-full AND clean-ci both succeed.
# The generated Markdown is intended to be committed with the milestone.
baseline:
	$(PYTHON) scripts/write_g0c_baseline.py

# Optional real-model smoke. It is intentionally outside CI because it costs
# money and requires an authenticated Claude Code CLI. It writes an ignored
# working artifact plus a commit-ready sanitized copy for evidence governance.
smoke-claude:
	$(PYTHON) scripts/smoke_claude.py \
		--output artifacts/smoke/claude-code.json \
		--publish-dir docs/baselines/smoke
