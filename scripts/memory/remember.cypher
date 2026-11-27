// Write one episode, the entities it mentions, and the facts taken from it,
// in one transaction: a failing statement rolls back the whole episode.
// Parameter $m: {episode: {id, session, agent, kind, at, text},
//                mentions: [{key, name}], facts: [{id, text, slot, about: [key], validFrom}]}
// recordedAt is the write time, so the latest write to a slot is its current
// fact whatever order the episodes' `at` times arrive in.
.begin
MERGE (ep:Episode {id: $m.episode.id})
  ON CREATE SET ep.session = $m.episode.session, ep.agent = $m.episode.agent,
                ep.kind = $m.episode.kind, ep.at = datetime($m.episode.at),
                ep.text = $m.episode.text
WITH ep
UNWIND $m.mentions AS m
MERGE (e:Entity {key: m.key}) ON CREATE SET e.name = m.name
MERGE (ep)-[:MENTIONS]->(e);

UNWIND $m.facts AS f
MATCH (ep:Episode {id: $m.episode.id})
MERGE (x:Fact {id: f.id})
  ON CREATE SET x:CurrentFact, x.text = f.text, x.slot = f.slot,
                x.validFrom = datetime(coalesce(f.validFrom, $m.episode.at)),
                x.recordedAt = datetime()
MERGE (x)-[:FROM]->(ep)
WITH x, f
UNWIND f.about AS key
MERGE (e:Entity {key: key}) ON CREATE SET e.name = key
MERGE (x)-[:ABOUT]->(e);

// Supersession: a new current fact closes the older current fact in its slot.
// A replayed episode finds its facts already closed or already newest, so it
// changes nothing.
UNWIND $m.facts AS f
MATCH (new:Fact {id: f.id}) WHERE new.closedAt IS NULL
MATCH (old:Fact {slot: new.slot})
WHERE old <> new AND old.closedAt IS NULL AND old.recordedAt <= new.recordedAt
SET old.validTo = new.validFrom, old.closedAt = new.recordedAt
REMOVE old:CurrentFact
MERGE (new)-[:SUPERSEDES]->(old)
RETURN new.slot AS slot, new.text AS current, old.text AS replaced;
.commit
