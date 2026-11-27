// Project memory schema. Every statement is idempotent.
CREATE CONSTRAINT entity_key IF NOT EXISTS FOR (e:Entity) REQUIRE e.key IS UNIQUE;
CREATE CONSTRAINT episode_id IF NOT EXISTS FOR (ep:Episode) REQUIRE ep.id IS UNIQUE;
CREATE CONSTRAINT fact_id IF NOT EXISTS FOR (f:Fact) REQUIRE f.id IS UNIQUE;
CREATE INDEX fact_slot IF NOT EXISTS FOR (f:Fact) ON (f.slot);
CREATE FULLTEXT INDEX fact_text IF NOT EXISTS FOR (f:Fact) ON EACH [f.text];
