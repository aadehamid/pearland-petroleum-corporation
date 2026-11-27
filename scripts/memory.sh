#!/usr/bin/env bash
# Shared project memory for every agent, stored in a Relate graph.
# Model and rules: .agents/skills/project-memory/SKILL.md.
#
# Usage:
#   scripts/memory.sh remember FILE|-   write one episode (JSON) and its facts
#   scripts/memory.sh recall WORDS...   full-text search over current facts
#   scripts/memory.sh about KEY         current facts about one entity
#   scripts/memory.sh history SLOT      every fact a slot has held, oldest first
#   scripts/memory.sh slots             slots that hold a current fact
#   scripts/memory.sh brief [N]         the N most recent current facts (default 20)
#   scripts/memory.sh check             fail if a slot holds more than one current fact
#   scripts/memory.sh init              create the store and its schema
#   scripts/memory.sh path              print the store path
#
# The store is a Relate directory store inside the repository's common git
# directory, so every worktree and every agent shares one memory and Git never
# tracks it. PPC_MEMORY_DB overrides the path.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cypher_dir="$here/memory"

store() {
  if [ -n "${PPC_MEMORY_DB:-}" ]; then
    printf '%s\n' "$PPC_MEMORY_DB"
  else
    printf '%s/relate-memory\n' "$(git -C "$here" rev-parse --path-format=absolute --git-common-dir)"
  fi
}

need_relate() {
  command -v relate >/dev/null 2>&1 && return 0
  echo "memory: relate is not installed. Install it with: curl -sSfL https://relatedb.ai/install.sh | bash" >&2
  exit 3
}

# Writes take the store's writer lock. Another agent may hold it for a moment,
# so retry a locked store (exit 5) a few times before failing.
write() {
  local attempt=1 status
  while :; do
    set +e
    relate query --database "$(store)" --mode jsonl "$@"
    status=$?
    set -e
    if [ "$status" -ne 5 ] || [ "$attempt" -ge 20 ]; then
      return "$status"
    fi
    attempt=$((attempt + 1))
    sleep 0.5
  done
}

read_query() {
  if [ ! -d "$(store)" ]; then
    echo "memory: no memory yet at $(store). Run: scripts/memory.sh init" >&2
    exit 0
  fi
  relate query --database "$(store)" --read-only --mode jsonl "$@"
}

# The schema is idempotent, so every write runs it first. Its notes are noise
# on success, so show them only when it fails.
init() {
  need_relate
  local out
  if ! out="$(write < "$cypher_dir/schema.cypher" 2>&1)"; then
    printf '%s\n' "$out" >&2
    return 1
  fi
  echo "memory: store ready at $(store)"
}

validate() {
  python3 - "$1" <<'PY'
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as fh:
        m = json.load(fh)
except (OSError, ValueError) as exc:
    sys.exit(f"memory: {path} is not readable JSON: {exc}")
errors = []
ep = m.get("episode") if isinstance(m, dict) else None
if not isinstance(ep, dict):
    errors.append("episode: missing object")
else:
    for key in ("id", "session", "agent", "kind", "at", "text"):
        if not isinstance(ep.get(key), str) or not ep[key].strip():
            errors.append(f"episode.{key}: missing string")
for i, e in enumerate(m.get("mentions", []) if isinstance(m, dict) else []):
    if not (isinstance(e, dict) and isinstance(e.get("key"), str) and isinstance(e.get("name"), str)):
        errors.append(f"mentions[{i}]: needs key and name strings")
facts = m.get("facts") if isinstance(m, dict) else None
if not isinstance(facts, list) or not facts:
    errors.append("facts: needs at least one fact")
else:
    for i, f in enumerate(facts):
        if not isinstance(f, dict):
            errors.append(f"facts[{i}]: not an object")
            continue
        for key in ("id", "text", "slot"):
            if not isinstance(f.get(key), str) or not f[key].strip():
                errors.append(f"facts[{i}].{key}: missing string")
        about = f.get("about")
        if not (isinstance(about, list) and about and all(isinstance(k, str) for k in about)):
            errors.append(f"facts[{i}].about: needs a non-empty list of entity keys")
if isinstance(m, dict):
    m.setdefault("mentions", [])
    if not errors:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(m, fh)
if errors:
    sys.exit("memory: invalid episode:\n  " + "\n  ".join(errors))
PY
}

remember() {
  need_relate
  local src="${1:?usage: scripts/memory.sh remember FILE|-}" tmp
  tmp="$(mktemp "${TMPDIR:-/tmp}/ppc-memory.XXXXXX")"
  trap 'rm -f "$tmp"' RETURN
  if [ "$src" = "-" ]; then cat > "$tmp"; else cat -- "$src" > "$tmp"; fi
  validate "$tmp"
  init > /dev/null
  write --fetch-params "m=$tmp" < "$cypher_dir/remember.cypher"
  python3 -c 'import json, sys; m = json.load(open(sys.argv[1])); print("memory: saved episode %s with %d fact(s)" % (m["episode"]["id"], len(m["facts"])))' "$tmp"
}

cmd="${1:-}"
[ $# -gt 0 ] && shift
case "$cmd" in
  init) init ;;
  path) store ;;
  remember) remember "$@" ;;
  recall)
    need_relate
    [ $# -gt 0 ] || { echo "usage: scripts/memory.sh recall WORDS..." >&2; exit 2; }
    read_query --param "q=$*" \
      'MATCH (f:Fact) SEARCH f IN (FULLTEXT INDEX fact_text FOR $q LIMIT 100) SCORE AS score
       WITH f, score WHERE f.closedAt IS NULL
       MATCH (f)-[:FROM]->(ep:Episode)
       RETURN f.slot AS slot, f.text AS memory, round(score, 3) AS score,
              ep.agent AS agent, toString(ep.at) AS learned, ep.text AS evidence
       ORDER BY score DESC LIMIT 10' ;;
  about)
    need_relate
    read_query --param "key=${1:?usage: scripts/memory.sh about KEY}" \
      'MATCH (e:Entity {key: $key})<-[:ABOUT]-(f:Fact)-[:FROM]->(ep:Episode)
       WHERE f.closedAt IS NULL
       RETURN f.slot AS slot, f.text AS memory, ep.agent AS agent, toString(ep.at) AS learned
       ORDER BY slot LIMIT 100' ;;
  history)
    need_relate
    read_query --param "slot=${1:?usage: scripts/memory.sh history SLOT}" \
      'MATCH (f:Fact {slot: $slot})-[:FROM]->(ep:Episode)
       RETURN f.text AS memory, toString(f.validFrom) AS validFrom, toString(f.validTo) AS validTo,
              toString(f.recordedAt) AS recorded, toString(f.closedAt) AS closed, ep.agent AS agent
       ORDER BY f.recordedAt LIMIT 100' ;;
  slots)
    need_relate
    read_query 'MATCH (f:Fact) WHERE f.closedAt IS NULL RETURN DISTINCT f.slot AS slot ORDER BY slot LIMIT 500' ;;
  brief)
    need_relate
    read_query --param "n=${1:-20}" \
      'MATCH (f:Fact)-[:FROM]->(ep:Episode) WHERE f.closedAt IS NULL
       RETURN f.slot AS slot, f.text AS memory, ep.agent AS agent, toString(ep.at) AS learned
       ORDER BY ep.at DESC LIMIT $n' ;;
  check)
    need_relate
    out="$(read_query \
      'MATCH (f:Fact) WHERE f.closedAt IS NULL
       WITH f.slot AS slot, count(*) AS current WHERE current > 1
       RETURN slot, current')"
    if [ -n "$out" ]; then
      echo "memory: slots with more than one current fact:" >&2
      printf '%s\n' "$out" >&2
      exit 1
    fi
    echo "memory: every slot holds at most one current fact" ;;
  *)
    sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    [ -z "$cmd" ] || [ "$cmd" = "help" ] || [ "$cmd" = "-h" ] || [ "$cmd" = "--help" ] || exit 2 ;;
esac
