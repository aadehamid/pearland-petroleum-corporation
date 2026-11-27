#!/usr/bin/env bash
# Shared project memory for every agent, stored in a Relate graph.
# Model and rules: .agents/skills/project-memory/SKILL.md.
#
# Usage:
#   scripts/memory.sh remember FILE|-   write one episode (JSON) and its facts
#   scripts/memory.sh recall WORDS...   full-text search over current facts
#   scripts/memory.sh about KEY         current facts about one entity
#   scripts/memory.sh history SLOT      every fact a slot has held, newest first
#   scripts/memory.sh slots             slots that hold a current fact
#   scripts/memory.sh brief [N]         the N most recent current facts (default 20)
#   scripts/memory.sh check             fail unless every slot holds exactly one current fact
#   scripts/memory.sh init              create the store and its schema
#   scripts/memory.sh path              print the store path
#
# The store is a Relate directory store inside the repository's common git
# directory, so every worktree and every agent shares one memory and Git never
# tracks it. PPC_MEMORY_DB overrides the path. Output is JSON lines.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cypher_dir="$here/memory"
tmp=""
trap '[ -z "$tmp" ] || rm -f "$tmp"' EXIT

store() {
  if [ -n "${PPC_MEMORY_DB:-}" ]; then
    printf '%s\n' "$PPC_MEMORY_DB"
    return
  fi
  local common
  common="$(git -C "$here" rev-parse --path-format=absolute --git-common-dir)"
  printf '%s/relate-memory\n' "$common"
}

need_relate() {
  command -v relate >/dev/null 2>&1 && return 0
  echo "memory: relate is not installed. Install it with: curl -sSfL https://relatedb.ai/install.sh | bash" >&2
  exit 3
}

# --param parses its value as JSON, so a bare `true` or `42` would bind as a
# boolean or a number. Encode every string parameter as a JSON string.
json_string() {
  python3 -c 'import json, sys; print(json.dumps(sys.argv[1]))' "$1"
}

# Writes take the store's writer lock. Another agent may hold it for a moment,
# so retry a locked store (exit 5) for up to 10 seconds. The script file is
# reopened on every attempt.
write() {
  local script="$1" db attempt=1 status
  shift
  db="$(store)"
  while :; do
    set +e
    relate query --database "$db" --mode jsonl "$@" < "$script"
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
  local db
  db="$(store)"
  if [ ! -d "$db" ]; then
    echo "memory: no memory yet at $db. Run: scripts/memory.sh init" >&2
    exit 0
  fi
  relate query --database "$db" --read-only --mode jsonl "$@"
}

# The schema is idempotent, so every write runs it first. Its notes are noise
# on success, so show them only when it fails.
init() {
  need_relate
  local out
  if ! out="$(write "$cypher_dir/schema.cypher" 2>&1)"; then
    printf '%s\n' "$out" >&2
    return 1
  fi
  echo "memory: store ready at $(store)"
}

validate() {
  python3 - "$1" <<'PY'
import json, re, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as fh:
        m = json.load(fh)
except (OSError, ValueError) as exc:
    sys.exit(f"memory: {path} is not readable JSON: {exc}")
KINDS = {"decision", "preference", "correction", "finding", "handoff", "tool_call"}
TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,9})?)?(Z|[+-]\d{2}:\d{2})")
errors = []

def text(obj, key, where):
    value = obj.get(key) if isinstance(obj, dict) else None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}.{key}: missing string")
        return None
    return value

def time(obj, key, where, required=True):
    if not required and obj.get(key) is None:
        return
    value = text(obj, key, where)
    if value is not None and not TIME.fullmatch(value):
        errors.append(f"{where}.{key}: not a UTC or offset datetime such as 2026-11-27T10:00:00Z")

if not isinstance(m, dict):
    sys.exit("memory: invalid episode:\n  top level: not an object")
ep = m.get("episode")
if not isinstance(ep, dict):
    errors.append("episode: missing object")
else:
    for key in ("id", "session", "agent", "text"):
        text(ep, key, "episode")
    time(ep, "at", "episode")
    if ep.get("kind") not in KINDS:
        errors.append(f"episode.kind: one of {', '.join(sorted(KINDS))}")
mentions = m.setdefault("mentions", [])
if not isinstance(mentions, list):
    errors.append("mentions: not a list")
    mentions = []
for i, e in enumerate(mentions):
    if not isinstance(e, dict):
        errors.append(f"mentions[{i}]: not an object")
        continue
    text(e, "key", f"mentions[{i}]")
    text(e, "name", f"mentions[{i}]")
facts = m.get("facts")
if not isinstance(facts, list) or not facts:
    errors.append("facts: needs at least one fact")
    facts = []
ids, slots = set(), set()
for i, f in enumerate(facts):
    where = f"facts[{i}]"
    if not isinstance(f, dict):
        errors.append(f"{where}: not an object")
        continue
    fid = text(f, "id", where)
    text(f, "text", where)
    slot = text(f, "slot", where)
    time(f, "validFrom", where, required=False)
    about = f.get("about")
    if not (isinstance(about, list) and about and all(isinstance(k, str) and k.strip() for k in about)):
        errors.append(f"{where}.about: needs a non-empty list of entity keys")
    if fid in ids:
        errors.append(f"{where}.id: repeats an earlier fact id")
    if slot in slots:
        errors.append(f"{where}.slot: repeats an earlier slot; one episode holds one fact per slot")
    ids.add(fid)
    slots.add(slot)
if errors:
    sys.exit("memory: invalid episode:\n  " + "\n  ".join(errors))
with open(path, "w", encoding="utf-8") as fh:
    json.dump(m, fh)
PY
}

# A fact id belongs to one episode. Reject an episode that reuses a fact id
# another episode already wrote.
check_fact_ids() {
  [ -d "$(store)" ] || return 0
  local clash
  clash="$(read_query --fetch-params "m=$1" \
    'UNWIND $m.facts AS f
     MATCH (x:Fact {id: f.id})-[:FROM]->(other:Episode) WHERE other.id <> $m.episode.id
     RETURN x.id AS fact, other.id AS episode')"
  if [ -n "$clash" ]; then
    echo "memory: invalid episode: fact ids already belong to another episode:" >&2
    printf '%s\n' "$clash" >&2
    exit 1
  fi
}

remember() {
  need_relate
  local src="${1:?usage: scripts/memory.sh remember FILE|-}"
  tmp="$(mktemp "${TMPDIR:-/tmp}/ppc-memory.XXXXXX")"
  if [ "$src" = "-" ]; then cat > "$tmp"; else cat -- "$src" > "$tmp"; fi
  validate "$tmp"
  check_fact_ids "$tmp"
  init > /dev/null
  write "$cypher_dir/remember.cypher" --fetch-params "m=$tmp"
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
    read_query --param "q=$(json_string "$*")" \
      'MATCH (f:CurrentFact) SEARCH f IN (FULLTEXT INDEX current_fact_text FOR $q LIMIT 10) SCORE AS score
       MATCH (f)-[:FROM]->(ep:Episode)
       RETURN f.slot AS slot, f.text AS memory, round(score, 3) AS score,
              ep.agent AS agent, ep.id AS episode, toString(ep.at) AS learned, ep.text AS evidence
       ORDER BY score DESC' ;;
  about)
    need_relate
    read_query --param "key=$(json_string "${1:?usage: scripts/memory.sh about KEY}")" \
      'MATCH (e:Entity {key: $key})<-[:ABOUT]-(f:CurrentFact)-[:FROM]->(ep:Episode)
       RETURN f.slot AS slot, f.text AS memory, ep.agent AS agent, ep.id AS episode,
              toString(ep.at) AS learned, ep.text AS evidence
       ORDER BY slot LIMIT 100' ;;
  history)
    need_relate
    read_query --param "slot=$(json_string "${1:?usage: scripts/memory.sh history SLOT}")" \
      'MATCH (f:Fact {slot: $slot})-[:FROM]->(ep:Episode)
       RETURN f.text AS memory, toString(f.validFrom) AS validFrom, toString(f.validTo) AS validTo,
              toString(f.recordedAt) AS recorded, toString(f.closedAt) AS closed,
              ep.agent AS agent, ep.id AS episode, ep.text AS evidence
       ORDER BY f.recordedAt DESC LIMIT 100' ;;
  slots)
    need_relate
    read_query 'MATCH (f:CurrentFact) RETURN DISTINCT f.slot AS slot ORDER BY slot LIMIT 500' ;;
  brief)
    need_relate
    n="${1:-20}"
    [[ "$n" =~ ^[1-9][0-9]{0,3}$ ]] || { echo "usage: scripts/memory.sh brief [N], N from 1 to 9999" >&2; exit 2; }
    read_query --param "n=$n" \
      'MATCH (f:CurrentFact)-[:FROM]->(ep:Episode)
       RETURN f.slot AS slot, f.text AS memory, ep.agent AS agent, ep.id AS episode,
              toString(ep.at) AS learned, ep.text AS evidence
       ORDER BY f.recordedAt DESC LIMIT $n' ;;
  check)
    need_relate
    out="$(read_query \
      'MATCH (f:Fact)
       WITH f.slot AS slot,
            sum(CASE WHEN f.closedAt IS NULL THEN 1 ELSE 0 END) AS current,
            sum(CASE WHEN (f.closedAt IS NULL) <> (f:CurrentFact) THEN 1 ELSE 0 END) AS mislabelled
       WHERE current <> 1 OR mislabelled > 0
       RETURN slot, current, mislabelled')"
    if [ -n "$out" ]; then
      echo "memory: slots without exactly one current fact, or with a mislabelled fact:" >&2
      printf '%s\n' "$out" >&2
      exit 1
    fi
    echo "memory: every slot holds exactly one current fact" ;;
  *)
    sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    [ -z "$cmd" ] || [ "$cmd" = "help" ] || [ "$cmd" = "-h" ] || [ "$cmd" = "--help" ] || exit 2 ;;
esac
