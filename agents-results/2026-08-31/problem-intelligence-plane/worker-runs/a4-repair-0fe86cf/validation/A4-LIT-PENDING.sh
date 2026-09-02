set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -m unittest -v tests.test_v02_literature_base
.venv/bin/python -m mypy --strict matharc/v02/literature_base.py
git diff --check -- matharc/v02/literature_base.py tests/test_v02_literature_base.py
