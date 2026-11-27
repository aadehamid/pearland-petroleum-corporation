#!/usr/bin/env bash
# Repository mechanical checks, in one place. CI and the pre-push hook both call
# this script so local and CI runs execute the same gates.
#
# Usage: scripts/check.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Git exports hook variables when running pre-push. Clear them so tests that call
# git init in temporary directories never modify this repository.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR GIT_PREFIX

tree_state() {
  python3 scripts/tree-state.py
}

before="$(tree_state)"

export PYTHONDONTWRITEBYTECODE=1

echo "== architecture package =="
python3 docs/enterprise-architecture/check_package.py
(cd docs/enterprise-architecture && python3 -m unittest test_check_package)

echo
echo "== check guard and pre-push hook =="
(cd scripts && python3 -m unittest test_tree_state test_pre_push_hook)

echo
echo "== shell syntax =="
while IFS= read -r script; do
  bash -n "$script"
  echo "  ok  $script"
done < <(git ls-files 'scripts/*.sh' 'scripts/hooks/*')

if [ "$(git config --get core.bare || true)" = "true" ]; then
  echo >&2
  echo "FAIL: core.bare is true after the checks: a test re-initialised this repository." >&2
  exit 1
fi

after="$(tree_state)"
if [ "$before" != "$after" ]; then
  echo >&2
  echo "FAIL: the checks changed the working tree." >&2
  git status --short >&2
  exit 1
fi

echo
echo "All checks passed."
