#!/usr/bin/env bash
set -euo pipefail

expected_head="cb1251d2a17315ae28efc1e14be1bba818c685f0"
test "$(git rev-parse HEAD)" = "$expected_head"
test "$(git rev-parse origin/main)" = "$expected_head"

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v \
  tests.test_v02_topic_observation_integrity \
  tests.test_v02_literature_base_integrity

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v \
  tests.test_v02_topic_observation \
  tests.test_v02_dogfood_archives \
  tests.test_v02_literature_base

PYTHONDONTWRITEBYTECODE=1 .venv/bin/mypy --no-incremental --strict \
  matharc/v02/topic_observation.py \
  matharc/v02/literature_base.py \
  matharc/v02/source_observation.py

git diff --check -- \
  matharc/v02/topic_observation.py \
  matharc/v02/literature_base.py \
  matharc/v02/source_observation.py \
  tests/test_v02_topic_observation_integrity.py \
  tests/test_v02_literature_base_integrity.py

test "$(shasum -a 256 tests/test_v02_topic_observation.py | awk '{print $1}')" = \
  "a6ac5fdb82f832e4eb14402d9727fcc5027a7574fb5d9765002d3016741fc9eb"
test "$(shasum -a 256 tests/test_v02_dogfood_archives.py | awk '{print $1}')" = \
  "e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873"

unexpected="$({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | sed \
  -e '/^matharc\/v02\/topic_observation.py$/d' \
  -e '/^matharc\/v02\/literature_base.py$/d' \
  -e '/^matharc\/v02\/source_observation.py$/d' \
  -e '/^tests\/test_v02_topic_observation_integrity.py$/d' \
  -e '/^tests\/test_v02_literature_base_integrity.py$/d' \
  -e '/^agents-results\/2026-08-31\/problem-intelligence-plane\/evidence\/a4-remediation\/transactional-replay-v3\/task.txt$/d' \
  -e '/^agents-results\/2026-08-31\/problem-intelligence-plane\/evidence\/a4-remediation\/transactional-replay-v3\/validation.sh$/d' \
  -e '/^agents-results\/2026-08-31\/problem-intelligence-plane\/evidence\/a4-remediation\/transactional-replay-v3\/artifacts\//d')"
test -z "$unexpected"
