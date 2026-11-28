#!/usr/bin/env python3
"""Independent verification tests for WP-2 Source Systems, OT/ICE, EDI CFG-0, and Atomic Outbox/Inbox (PO-03).

Covers:
- Atomic source DB + OutboxEntry commit (crash before commit leaves zero partial rows)
- PO-03 Crash Point 1 (before NATS ack): identical redelivery returns IDEMPOTENT_DUPLICATE with zero double effect
- Idempotent conflict quarantine for conflicting digest under same delivery_key (5 retries -> 1 quarantine row)
- Server-tracked bidirectional revision monotonicity (forward gaps AND regressions/duplicates quarantined)
- PO-03 Crash Point 2 with pre-pinned batch rows: new row B staged during crash window is NOT dropped on retry
- OT-01 ambiguous/unregistered tag rejection, OT-02 deadband + Bad quality bypass, OT-03 NBIRTH(seq=0)/DBIRTH(seq>=1)
  with restart buffer persistence and no invented readings, OT-DELAY-01 visibility cutoff using real WP-1b OT tags
- EDI CFG-0 adoption against real WP-1b fixtures/golden/cfg0_dexpi_topology.json, non-vacuous B7 digest check,
  idempotent request_id receipts + conflict detection, and dangling-edge rejection
- Automated AST import check confirming zero hidden-truth imports in integration/, ot/, and source-systems/
"""
from __future__ import annotations

import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from integration.edi_adoption import EDIAdoptionRegistry, canonical_cfg0_digest
from integration.outbox_inbox_service import AtomicStagingInboxService
from ot.sparkplug_ice_pipeline import AmbiguousTagError, SparkplugOTPublisher, filter_visible_ot_events

REPO_ROOT = Path(__file__).resolve().parents[1]
CFG0_PATH = REPO_ROOT / "fixtures" / "golden" / "cfg0_dexpi_topology.json"
OT_TAGS_PATH = REPO_ROOT / "fixtures" / "golden" / "refinery_a_ot_tags.yaml"


def _load_outbox_store_module():
    path = REPO_ROOT / "source-systems" / "refinery" / "outbox_store.py"
    spec = importlib.util.spec_from_file_location("ppc_outbox_store", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules["ppc_outbox_store"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestWP2SourcesOTIntegration(unittest.TestCase):
    def test_po03_atomic_outbox_crash_points_1_and_2_conflicts_and_reordering(self):
        outbox_mod = _load_outbox_store_module()
        with tempfile.TemporaryDirectory(prefix="ppc-wp2-") as tmp:
            src_store = outbox_mod.TransactionalOutboxSourceStore(Path(tmp) / "refinery.db", "refinery_sqlite")
            inbox = AtomicStagingInboxService(Path(tmp) / "staging_inbox.db")
            try:
                # 1. Crash BEFORE commit rolls back both domain row and outbox row
                with self.assertRaises(RuntimeError):
                    src_store.commit_with_outbox(
                        branch_id="baseline",
                        partition_key="unit:4B",
                        source_tx_id="TX-CRASH-001",
                        event_id="EV-CRASH-001",
                        delivery_key="refinery_sqlite:baseline:unit:4B:crash1",
                        native_entity_key="4B",
                        source_revision=1,
                        event_type="HCU_DERATE_EVENT",
                        effective_at_utc="2026-06-15T08:15:00Z",
                        recorded_at_utc="2026-06-15T08:15:00Z",
                        payload={"compressor_circ_fraction": 0.75},
                        inject_crash_before_commit=True,
                    )
                self.assertEqual(src_store.count_native_records(), 0)
                self.assertEqual(len(src_store.fetch_pending_outbox()), 0)

                # 2. Successful atomic commit emits revision 1
                rec1 = src_store.commit_with_outbox(
                    branch_id="baseline",
                    partition_key="unit:4B",
                    source_tx_id="TX-OK-001",
                    event_id="EV-OK-001",
                    delivery_key="refinery_sqlite:baseline:unit:4B:rev1",
                    native_entity_key="4B",
                    event_type="HCU_DERATE_EVENT",
                    effective_at_utc="2026-06-15T08:15:00Z",
                    recorded_at_utc="2026-06-15T08:15:00Z",
                    payload={"compressor_circ_fraction": 0.75},
                    source_revision=1,
                )
                ev1 = {
                    "delivery_key": rec1.delivery_key,
                    "event_id": rec1.event_id,
                    "source_system": rec1.source_system,
                    "branch_id": rec1.branch_id,
                    "partition_key": rec1.partition_key,
                    "source_sequence": rec1.source_sequence,
                    "source_revision": rec1.source_revision,
                    "event_type": rec1.event_type,
                    "effective_at_utc": rec1.effective_at_utc,
                    "recorded_at_utc": rec1.recorded_at_utc,
                    "published_at_utc": "2026-06-15T08:15:30Z",
                    "payload_digest": rec1.payload_digest,
                    "payload_json": rec1.payload_json,
                }

                # 3. PO-03 Crash Point 1: DB commit succeeds, NATS ack fails -> redelivery is IDEMPOTENT_DUPLICATE
                with self.assertRaises(RuntimeError):
                    inbox.consume_event(ev1, inject_crash_after_staging_before_ack=True)
                self.assertEqual(inbox.staging_count(), 1)
                redeliv = inbox.consume_event(ev1)
                self.assertEqual(redeliv.status, "IDEMPOTENT_DUPLICATE")
                self.assertEqual(inbox.staging_count(), 1)

                # 4. Same delivery_key + different digest -> idempotent CONFLICT_QUARANTINED (5 retries -> 1 row)
                tampered = dict(ev1)
                tampered["payload_digest"] = "0" * 64
                for _ in range(5):
                    conflict = inbox.consume_event(tampered)
                    self.assertEqual(conflict.status, "CONFLICT_QUARANTINED")
                self.assertEqual(inbox.quarantine_count(), 1)
                self.assertEqual(inbox.staging_count(), 1)

                # 5. Server-tracked revision monotonicity (no caller parameter needed!):
                # Forward gap (rev=3 after rev=1) AND regression (rev=1 under new delivery_key) BOTH quarantine
                ooo = dict(ev1)
                ooo["delivery_key"] = "refinery_sqlite:baseline:unit:4B:rev3"
                ooo["event_id"] = "EV-OOO-3"
                ooo["source_sequence"] = 2
                ooo["source_revision"] = 3
                self.assertEqual(inbox.consume_event(ooo).reason, "OUT_OF_ORDER_REVISION")

                reg = dict(ev1)
                reg["delivery_key"] = "refinery_sqlite:baseline:unit:4B:rev1-dup"
                reg["event_id"] = "EV-REG-1"
                reg["source_sequence"] = 2
                reg["source_revision"] = 1
                self.assertEqual(inbox.consume_event(reg).reason, "STALE_OR_DUPLICATE_REVISION")
                self.assertEqual(inbox.staging_count(), 1)

                # 6. PO-03 Crash Point 2 with new row B arriving during crash window:
                # txn v1 commits row 1 -> crashes before mark -> row 2 arrives -> retry v1 marks ONLY row 1!
                committed_batches: dict[tuple[str, int], list[dict]] = {}

                def idempotent_delta_sink(*, table_name, rows, txn_app_id, txn_version):
                    key = (txn_app_id, txn_version)
                    if key not in committed_batches:
                        committed_batches[key] = list(rows)

                with self.assertRaises(RuntimeError):
                    inbox.publish_staging_to_delta_idempotent(
                        txn_app_id="wp2_silver_pub",
                        txn_version=1,
                        table_name="silver_refinery_events",
                        source_system="refinery_sqlite",
                        branch_id="baseline",
                        sink_commit_fn=idempotent_delta_sink,
                        inject_crash_after_sink_before_mark=True,
                    )

                # New event B (revision 2) arrives BEFORE txn v1 retries!
                ev2 = dict(ev1)
                ev2["delivery_key"] = "refinery_sqlite:baseline:unit:4B:rev2"
                ev2["event_id"] = "EV-OK-2"
                ev2["source_sequence"] = 2
                ev2["source_revision"] = 2
                self.assertEqual(inbox.consume_event(ev2).status, "APPLIED")
                self.assertEqual(inbox.staging_count(), 2)

                # Retry txn v1 completes ledger ONLY for pinned row 1; row 2 MUST remain unpublished!
                pub1 = inbox.publish_staging_to_delta_idempotent(
                    txn_app_id="wp2_silver_pub",
                    txn_version=1,
                    table_name="silver_refinery_events",
                    source_system="refinery_sqlite",
                    branch_id="baseline",
                    sink_commit_fn=idempotent_delta_sink,
                )
                self.assertEqual(pub1["status"], "PUBLISHED")
                self.assertEqual(pub1["row_count"], 1)
                self.assertEqual(inbox.unpublished_count(), 1)

                # Next txn v2 publishes row 2 cleanly (zero lost rows!)
                pub2 = inbox.publish_staging_to_delta_idempotent(
                    txn_app_id="wp2_silver_pub",
                    txn_version=2,
                    table_name="silver_refinery_events",
                    source_system="refinery_sqlite",
                    branch_id="baseline",
                    sink_commit_fn=idempotent_delta_sink,
                )
                self.assertEqual(pub2["status"], "PUBLISHED")
                self.assertEqual(pub2["row_count"], 1)
                self.assertEqual(inbox.unpublished_count(), 0)
            finally:
                src_store.close()
                inbox.close()

    def test_ot01_to_ot03_and_ot_delay01_using_real_wp1b_ot_schedule(self):
        schedule = yaml.safe_load(OT_TAGS_PATH.read_text(encoding="utf-8"))
        # OT-01: duplicate tag rejected
        with self.assertRaises(AmbiguousTagError):
            SparkplugOTPublisher({"tags": [schedule["tags"][0], schedule["tags"][0]]})

        with tempfile.TemporaryDirectory(prefix="ppc-wp2-ot-") as tmp:
            buf_file = Path(tmp) / "ot_buffer.json"
            pub = SparkplugOTPublisher(schedule, buffer_path=buf_file)
            # Unregistered tag rejected
            with self.assertRaises(AmbiguousTagError):
                pub.ingest_sample(
                    "REFA.UNKNOWN.TAG", 1.0, "Good",
                    "2026-06-15T08:00:00Z", "2026-06-15T08:00:00Z", "2026-06-15T08:00:00Z",
                )

            # Initial birth with no samples emits NBIRTH (seq=0) only — never invents 0.0 / Uncertain DBIRTHs
            b1 = pub.connect_and_birth("2026-06-15T08:00:00Z")
            self.assertEqual(len(b1), 1)
            self.assertEqual(b1[0].message_type, "NBIRTH")
            self.assertEqual(b1[0].seq, 0)
            self.assertEqual(b1[0].bd_seq, 1)

            tag = "REFA.HCU.K201.SI_4110.PV"  # eu_range [0, 110], deadband_pct 0.10 -> deadband 0.11
            e1 = pub.ingest_sample(tag, 100.0, "Good", "2026-06-15T08:01:00Z", "2026-06-15T08:01:00Z", "2026-06-15T08:01:01Z")
            self.assertIsNotNone(e1)
            self.assertEqual(e1.seq, 1)
            self.assertEqual(e1.equipment_id, "K-201")

            # OT-02: small change inside deadband suppressed
            self.assertIsNone(
                pub.ingest_sample(tag, 100.05, "Good", "2026-06-15T08:02:00Z", "2026-06-15T08:02:00Z", "2026-06-15T08:02:01Z")
            )
            # Bad quality transition bypasses deadband immediately even with identical value
            bad = pub.ingest_sample(tag, 100.05, "Bad", "2026-06-15T08:03:00Z", "2026-06-15T08:03:00Z", "2026-06-15T08:03:01Z")
            self.assertIsNotNone(bad)
            self.assertEqual(bad.quality, "Bad")

            # OT-03: Disconnect, buffer sample offline, simulate full process restart -> NBIRTH + DBIRTH restores buffered sample!
            pub.simulate_broker_disconnect()
            self.assertIsNone(
                pub.ingest_sample(tag, 75.0, "Good", "2026-06-15T08:15:00Z", "2026-06-15T08:15:00Z", "2026-06-15T08:15:30Z")
            )
            pub_restarted = SparkplugOTPublisher(schedule, buffer_path=buf_file)
            b2 = pub_restarted.connect_and_birth("2026-06-15T08:15:30Z")
            self.assertEqual(b2[0].message_type, "NBIRTH")
            self.assertEqual(b2[0].bd_seq, 2)
            self.assertEqual(b2[0].seq, 0)
            dbirth = [e for e in b2 if e.message_type == "DBIRTH"]
            self.assertEqual(len(dbirth), 1)
            self.assertEqual(dbirth[0].tag_name, tag)
            self.assertEqual(dbirth[0].value, 75.0)
            self.assertEqual(dbirth[0].seq, 1)

            # OT-DELAY-01: published at 08:15:30 invisible at 08:15:00, visible at 08:16:00
            self.assertEqual(len(filter_visible_ot_events(dbirth, "2026-06-15T08:15:00Z")), 0)
            self.assertEqual(len(filter_visible_ot_events(dbirth, "2026-06-15T08:16:00Z")), 1)

    def test_edi_cfg0_adoption_b7_real_fixture_idempotency_and_dangling_rejection(self):
        cfg0_raw = json.loads(CFG0_PATH.read_text(encoding="utf-8"))
        upstream_digest = canonical_cfg0_digest(cfg0_raw)

        reg = EDIAdoptionRegistry()
        r1 = reg.adopt_cfg0_topology(
            CFG0_PATH,
            request_id="REQ-CFG0-001",
            world_id="WORLD-PPC-V1",
            branch_id="baseline",
            authorized_actor="usr-ref-ops",
            expected_cfg0_digest=upstream_digest,
            recorded_at_utc="2026-06-15T00:01:00Z",
        )
        self.assertEqual(r1["outcome"], "ADOPTED")
        self.assertTrue(r1["b7_digest_parity"])
        self.assertEqual(r1["adopted_digest"], upstream_digest)

        # Idempotent replay of same request_id returns identical receipt (including recorded_at_utc)
        r1_replay = reg.adopt_cfg0_topology(
            CFG0_PATH,
            request_id="REQ-CFG0-001",
            world_id="WORLD-PPC-V1",
            branch_id="baseline",
            authorized_actor="usr-ref-ops",
            expected_cfg0_digest=upstream_digest,
            recorded_at_utc="2026-06-15T00:99:00Z",
        )
        self.assertEqual(r1_replay, r1)

        # Non-vacuous B7 mismatch MUST fail closed
        with self.assertRaises(ValueError):
            reg.adopt_cfg0_topology(
                CFG0_PATH,
                request_id="REQ-CFG0-BAD-DIGEST",
                world_id="WORLD-PPC-V1",
                branch_id="baseline",
                authorized_actor="usr-ref-ops",
                expected_cfg0_digest="0" * 64,
            )

        with tempfile.TemporaryDirectory(prefix="ppc-wp2-edi-") as tmp:
            # Different payload under existing request_id MUST return CONFLICT
            alt = dict(cfg0_raw)
            alt["equipment"] = list(cfg0_raw["equipment"]) + [{"tag": "TK-EXTRA", "class": "StorageTank", "site_id": "SITE-REF-A"}]
            alt_path = Path(tmp) / "alt_cfg0.json"
            alt_path.write_text(json.dumps(alt), encoding="utf-8")
            conflict = reg.adopt_cfg0_topology(
                alt_path,
                request_id="REQ-CFG0-001",
                world_id="WORLD-PPC-V1",
                branch_id="baseline",
                authorized_actor="usr-ref-ops",
                expected_cfg0_digest=canonical_cfg0_digest(alt),
            )
            self.assertEqual(conflict["outcome"], "CONFLICT")

            # Dangling endpoint MUST fail closed
            bad = dict(cfg0_raw)
            bad["piping_connections"] = [{"id": "LINE-BAD", "from": "CDU", "to": "NONEXISTENT", "pumps": []}]
            bad_path = Path(tmp) / "bad_cfg0.json"
            bad_path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(ValueError):
                reg.adopt_cfg0_topology(
                    bad_path,
                    request_id="REQ-CFG0-DANGLE",
                    world_id="WORLD-PPC-V1",
                    branch_id="baseline",
                    authorized_actor="usr-ref-ops",
                    expected_cfg0_digest=canonical_cfg0_digest(bad),
                )

    def test_zero_hidden_truth_imports_in_integration_ot_and_source_systems(self):
        forbidden = ("generators", "world_kernel", "evaluation", "hidden")
        for folder in ("integration", "ot", "source-systems"):
            for py_file in (REPO_ROOT / folder).rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            for tok in forbidden:
                                self.assertNotIn(tok, alias.name.lower(), f"Forbidden import {alias.name} in {py_file}")
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        for tok in forbidden:
                            self.assertNotIn(tok, node.module.lower(), f"Forbidden import {node.module} in {py_file}")


if __name__ == "__main__":
    unittest.main()
