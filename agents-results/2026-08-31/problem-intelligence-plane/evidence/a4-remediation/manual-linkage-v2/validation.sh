#!/bin/sh
set -eu
python3 -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives
python3 -m unittest discover -s tests -p 'test_v02*.py'
python3 -m py_compile matharc/v02/topic_observation.py tests/test_v02_topic_observation.py
git diff --check
