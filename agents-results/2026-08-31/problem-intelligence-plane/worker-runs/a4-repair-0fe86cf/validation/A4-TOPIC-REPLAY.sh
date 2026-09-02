set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -m unittest -v tests.test_v02_topic_observation_integrity tests.test_v02_artifact_store_durability tests.test_v02_topic_observation tests.test_v02_dogfood_archives
.venv/bin/python -m mypy --strict matharc/v02/topic_observation.py
git diff --check -- matharc/v02/topic_observation.py tests/test_v02_topic_observation_integrity.py tests/test_v02_artifact_store_durability.py
test "$(shasum -a 256 tests/test_v02_topic_observation.py | awk '{print $1}')" = "bccdbb46c5bb8bb256d7f2c403e3fcbcf7c6c51976134fd8c18b23bc4b2ce497"
test "$(shasum -a 256 tests/test_v02_dogfood_archives.py | awk '{print $1}')" = "345a2c94299df3f001757606ac2c9db6f7243a20dd42d150a77360e28c678242"
