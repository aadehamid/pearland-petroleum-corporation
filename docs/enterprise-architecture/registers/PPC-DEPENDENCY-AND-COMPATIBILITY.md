# PPC dependency and compatibility register

Draft gate list, 2026-11-25. [ARCH-000 §8](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md#8-versioned-dependency-and-scenario-manifest-policy) defines the proposed top-level manifest. The inspected commit pins are in the [source register](PPC-SOURCE-REGISTER.md), not approved PPC bindings. This table records compatibility work.

| Dependency | Required use | Maturity at inspected baseline | Compatibility proof still needed |
|---|---|---|---|
| EPM modules | KPI, process and semantic meaning | Module-specific status needed | IRI, SHACL, formula and grain parity |
| DS_Business_Process | Generic process concepts after approval | Pending; branch pointer matched KPI 1.2 | Released digest and migration |
| ICE | L0 observation and future mapping | L0 inspected; mapping pending | Tag, unit, quality and identity fixture |
| EDI | Engineering publication and adoption | Bounded structured slice inspected | Revision, topology and recovery fixture |
| ECE | Evidence and evaluation pattern | Published reusable schema not established | Historical access and claim contract |
| Public ontologies | PPC-019 candidates for mapped reuse | Candidate terms; no approved local binding | License, release, dependency closure and mapping review |
| EIA/NOAA/EPA/PHMSA feeds | Public observations with source and vintage | Feed-specific verification pending | Timestamp, quality, license and fictional exposure separation |
| PPC world/source/data | Fictional execution | Draft specifications | Replay, reconciliation and consistent release |

Fail a qualified release if a required package has no approved identity or the tested combination differs from the activation manifest. The first slice may defer optional services only with an explicit scope decision; it may not label a pending dependency approved.
