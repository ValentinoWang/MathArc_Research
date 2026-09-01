#!/usr/bin/env bash
set -euo pipefail
exec codex exec -C "$(pwd -P)" --skip-git-repo-check --sandbox danger-full-access --model gpt-5.6-sol -c 'model_reasoning_effort="low"' "$1"
