# PPC-PLATFORM-001 — Infrastructure, Security and Operations

| Control | Value |
|---|---|
| ID / status | PPC-PLATFORM-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-002](../../PPC-002_Enterprise_Architecture_and_Technology_Stack.md), [PPC-009](../../PPC-009_Metadata_Governance_Quality_and_Observability.md), [PPC-013](../../PPC-013_Cloudflare_R2_Durability_and_Project_Storage_Standard.md), [PPC-014](../../PPC-014_Implementation_Roadmap_and_Build_Runbook.md); ADR-003, 004, 007, 017, 018 |
| Contract | Versioned service and release configuration → isolated operation and recoverable state |

## 1. Placement and security boundary

PPC-002 records the baseline stack. R2 is durable object storage, not a transactional database. Source databases own native records. The analytical store owns released products. Neo4j Community owns a derived graph. D1 owns workflow state in the baseline. A proposed exe.dev deployment and possible Delta/Databricks paths need entitlement, capacity and recovery evidence before selection. Cloudflare R2 is an explicit exception to the open-source preference discussed at T79. No production or real OT access is authorized by this draft.

`ServiceDescriptor` records service ID, image/source digest, configuration digest, environment, branch scope, data authority, upstream release pins, secret references, network routes, health checks, backup policy and recovery objective. `OperationRecord` adds actor, action, time, result and evidence locator. `BackupManifest` records consistent source cut, object hashes, database log position, encryption key reference and restore test. Secrets are never embedded in manifests or documents. Roles separate world truth, source apps, integration, evidence retrieval, hidden evaluation and approval execution. Each service may read only its assigned scope.

Deployment lifecycle is `DEFINED → DEPLOYED → HEALTHY → DEGRADED → RECOVERING → VERIFIED`; a health endpoint alone does not mean a release is qualified. Recovery must establish source database and outbox/inbox positions, table manifests, world checkpoint and graph rebuild boundary before advertising readiness. Monitoring tracks lag, rejected mappings, replay errors, release state and access denial without logging restricted payloads.

## 2. Synthetic recovery fixture

In a `SYNTHETIC` quality-rejection run, a source ticket commits at 08:05 and its outbox message is pending. A worker fails at 08:06. Restore from a backup at 08:00 plus the source log, then drain the outbox. The expected result is one ticket and one applied downstream business effect. A published analytical release must remain at its prior watermark until reconciliation succeeds. A graph may rebuild from that release; it cannot create another physical receipt. A compromised retrieval role must fail to read canonical world or hidden-evaluation objects. A sibling branch restore cannot adopt baseline state without explicit branch provenance.

## 3. Qualification and options

Record restore duration, data-loss bound, integrity hashes, source log positions, failed-secret and denied-route tests, backup corruption, replay and cross-service cut consistency. Verify R2 retention and recovery with a drill, not a storage setting alone. No deployment, restore or entitlement test is claimed. Alternatives include one exe.dev host versus isolated service hosts, DuckLake versus Delta analytical history, and an early catalog versus later catalog adoption. Compare them by isolation, recovery, cost and actual entitlement before changing ADR-007, 017 or 018. T46–52, T78–82, T85–87 and T119–121 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) are the proposals and owner preferences; the repository baseline remains distinct.
