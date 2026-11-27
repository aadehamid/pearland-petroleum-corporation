-- PPC PostgreSQL Slice 1 Initialization (ADR-0046, ADR-0047, ADR-0055 G2-c)
-- Consolidates CTRM, TimescaleDB historian, pgvector evidence, Dagster metadata,
-- atomic Silver staging + InboxReceipt, and workflow/approval/RBAC/LangGraph state
-- into one PostgreSQL instance (Cloudflare D1 is not used in v1).

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS ctrm;
CREATE SCHEMA IF NOT EXISTS historian;
CREATE SCHEMA IF NOT EXISTS evidence;
CREATE SCHEMA IF NOT EXISTS dagster;
CREATE SCHEMA IF NOT EXISTS silver_staging;
CREATE SCHEMA IF NOT EXISTS workflow_state;
