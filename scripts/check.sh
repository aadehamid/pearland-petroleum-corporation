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
echo "== ADR graph =="
(cd scripts && python3 -m unittest -q test_adr_graph)
python3 scripts/adr_graph.py check
python3 scripts/adr_graph.py summary

echo
echo "== physical-model consistency graph =="
uv run --no-project --with pyyaml python3 -m unittest -q scripts/test_physical_graph.py
uv run --no-project --with pyyaml python3 scripts/physical_graph.py check
uv run --no-project --with pyyaml python3 scripts/physical_graph.py summary

echo
echo "== project memory =="
command -v relate >/dev/null 2>&1 || echo "  skip  relate not installed; the memory tests that need it skip, the rest run"
(cd scripts && python3 -m unittest test_memory)

echo
echo "== WP-0 contracts, schemas, adapters, semantic, and infra =="
uv run --no-project --with jsonschema --with referencing --with pyyaml --with rdflib --with pyshacl \
  python3 -m unittest tests/test_wp0_contracts.py

echo
echo "== WP-1a public data ingest contracts =="
uv run --no-project --with jsonschema python3 -m unittest tests/test_public_ingest.py

echo
echo "== WP-4A backup op-budget, recovery-gap checker, and SQLite restore drill =="
python3 -m unittest -q tests/test_wp4a_backup_recovery.py

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  (cd infra && docker compose --profile all config -q) && echo "  ok  infra/docker-compose.yml parses"
else
  echo "  skip  docker compose not available; YAML structure tests above still read docker-compose.yml"
fi

echo
echo "== WP-1b design basis, CFG-0 topology, and OT tags =="
uv run --no-project --with pyyaml python3 -m unittest tests/test_wp1b_design_basis.py

echo
echo "== WP-3 Delta Lake KPI store, EPM bindings, Neo4j RDF projection, and INFO-001 reader-as-of =="
uv run --no-project --with deltalake --with duckdb --with pyarrow --with pyyaml --with rdflib --with pyshacl \
  python3 -m unittest tests/test_wp3_lakehouse_semantic_evidence.py

echo
echo "== WP-8A DuckDB-vs-Databricks KPI parity and WP-8B Certified WorldExportBundle v1 =="
uv run --no-project --with jsonschema python3 -m unittest tests/test_wp8_parity_and_bundle.py

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
