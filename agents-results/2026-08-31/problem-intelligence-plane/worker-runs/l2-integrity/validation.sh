#!/usr/bin/env bash
set -euo pipefail
python3 -m unittest -v tests.test_v02_source_observation tests.test_v02_literature_base
python3 -m unittest discover -s tests
git diff --check
