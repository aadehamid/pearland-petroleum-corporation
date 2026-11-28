#!/usr/bin/env python3
"""Independent verification tests for WP-2 Source Systems, OT/ICE, EDI CFG-0, and Atomic Outbox/Inbox (PO-03).

Covers:
- Atomic source DB + OutboxEntry commit (crash before commit leaves zero partial rows)
- PO-03 Crash Point 1 (before NATS ack): identical redelivery returns IDEMPOTENT_DUPLICATE with zero double effect
- Idempotent conflict quarantine for conflicting digest under same delivery_key (5 retries -> 1 quarantine row)
- Server-tracked bidirectional revision monotonicity (forward gaps AND regressions/duplicates quarantined)
- PO-03 Crash Point 2 with exclusive pre-pinned batch ownership:
  (a) crash after pin before sink: txn v2 cannot steal or double-publish txn v1's pinned row
  (b) crash after sink before mark: new row B staged during crash window is NOT dropped on txn v1 retry
- OT-01 ambiguous/unregistered tag rejection, OT-02 deadband + Bad quality bypass, OT-03 NBIRTH(seq=0)/DBIRTH(seq>=1)
  with atomic crash-safe restart buffer persistence and explicit corrupt-buffer loss signaling, OT-DELAY-01 cutoff
- EDI CFG-0 adoption against real WP-1b fixtures/golden/cfg0_dexpi_topology.json with independently pinned
  literal SHA-256 digest, canonicalization sensitivity test, SQLite cross-restart idempotency,
  expected_prior_configuration enforcement (EDI-001 §3), scope vs payload CONFLICT reasons, and dangling-edge rejection
- Automated AST check confirming zero static or dynamic hidden-truth imports in integration/, ot/, and source-systems/
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

# Independently pinned SHA-256 canonical digest of WP-1b fixtures/golden/cfg0_dexpi_topology.json (39 equip, 6 conns)
PINNED_WP1B_CFG0_DIGEST = "f355152dd35019f0d83245eb1b13c754a4172d99e1b24c47a97402f76a8fb2b0"


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

                # 5. Server-tracked revision monotonicity: forward gap AND regression BOTH quarantine
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

                # 6. PO-03 Crash Point 2a (crash AFTER pin BEFORE sink):
                # txn v1 pins row 1 and crashes before calling sink -> txn v2 MUST NOT claim row 1!
                committed_batches: dict[tuple[str, int], list[dict]] = {}
                committed_delivery_keys: list[str] = []

                def idempotent_delta_sink(*, table_name, rows, txn_app_id, txn_version):
                    key = (txn_app_id, txn_version)
                    if key not in committed_batches:
                        committed_batches[key] = list(rows)
                        committed_delivery_keys.extend(r["delivery_key"] for r in rows)

                with self.assertRaises(RuntimeError):
                    inbox.publish_staging_to_delta_idempotent(
                        txn_app_id="wp2_silver_pub",
                        txn_version=1,
                        table_name="silver_refinery_events",
                        source_system="refinery_sqlite",
                        branch_id="baseline",
                        sink_commit_fn=idempotent_delta_sink,
                        inject_crash_after_pin_before_sink=True,
                    )
                # Another txn v99 trying to publish while txn v1 owns row 1 sees NO_PENDING_ROWS (zero cross-txn stealing!)
                steal_attempt = inbox.publish_staging_to_delta_idempotent(
                    txn_app_id="wp2_silver_pub",
                    txn_version=99,
                    table_name="silver_refinery_events",
                    source_system="refinery_sqlite",
                    branch_id="baseline",
                    sink_commit_fn=idempotent_delta_sink,
                )
                self.assertEqual(steal_attempt["status"], "NO_PENDING_ROWS")
                self.assertEqual(committed_delivery_keys, [])

                # 7. PO-03 Crash Point 2b (crash AFTER sink BEFORE mark):
                # txn v1 retries, commits row 1, crashes before mark -> row 2 arrives -> retry v1 marks ONLY row 1!
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

                ev2 = dict(ev1)
                ev2["delivery_key"] = "refinery_sqlite:baseline:unit:4B:rev2"
                ev2["event_id"] = "EV-OK-2"
                ev2["source_sequence"] = 2
                ev2["source_revision"] = 2
                self.assertEqual(inbox.consume_event(ev2).status, "APPLIED")
                self.assertEqual(inbox.staging_count(), 2)

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

                # Next txn v2 publishes row 2 cleanly (zero lost rows and zero cross-txn duplicates!)
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
                self.assertEqual(
                    committed_delivery_keys,
                    ["refinery_sqlite:baseline:unit:4B:rev1", "refinery_sqlite:baseline:unit:4B:rev2"],
                )
            finally:
                src_store.close()
                inbox.close()

    def test_ot01_to_ot03_and_ot_delay01_using_real_wp1b_ot_schedule(self):
        schedule = yaml.safe_load(OT_TAGS_PATH.read_text(encoding="utf-8"))
        with self.assertRaises(AmbiguousTagError):
            SparkplugOTPublisher({"tags": [schedule["tags"][0], schedule["tags"][0]]})

        with tempfile.TemporaryDirectory(prefix="ppc-wp2-ot-") as tmp:
            buf_file = Path(tmp) / "ot_buffer.json"
            pub = SparkplugOTPublisher(schedule, buffer_path=buf_file)
            with self.assertRaises(AmbiguousTagError):
                pub.ingest_sample(
                    "REFA.UNKNOWN.TAG", 1.0, "Good",
                    "2026-06-15T08:00:00Z", "2026-06-15T08:00:00Z", "2026-06-15T08:00:00Z",
                )

            b1 = pub.connect_and_birth("2026-06-15T08:00:00Z")
            self.assertEqual(len(b1), 1)
            self.assertEqual(b1[0].message_type, "NBIRTH")
            self.assertEqual(b1[0].seq, 0)
            self.assertEqual(b1[0].bd_seq, 1)

            tag = "REFA.HCU.K201.SI_4110.PV"
            e1 = pub.ingest_sample(tag, 100.0, "Good", "2026-06-15T08:01:00Z", "2026-06-15T08:01:00Z", "2026-06-15T08:01:01Z")
            self.assertIsNotNone(e1)
            self.assertEqual(e1.seq, 1)
            self.assertEqual(e1.equipment_id, "K-201")

            self.assertIsNone(
                pub.ingest_sample(tag, 100.05, "Good", "2026-06-15T08:02:00Z", "2026-06-15T08:02:00Z", "2026-06-15T08:02:01Z")
            )
            bad = pub.ingest_sample(tag, 100.05, "Bad", "2026-06-15T08:03:00Z", "2026-06-15T08:03:00Z", "2026-06-15T08:03:01Z")
            self.assertIsNotNone(bad)
            self.assertEqual(bad.quality, "Bad")

            # Disconnect, buffer sample offline, simulate full restart -> NBIRTH + DBIRTH restores buffered sample
            pub.simulate_broker_disconnect()
            self.assertIsNone(
                pub.ingest_sample(tag, 75.0, "Good", "2026-06-15T08:15:00Z", "2026-06-15T08:15:00Z", "2026-06-15T08:15:30Z")
            )
            pub_restarted = SparkplugOTPublisher(schedule, buffer_path=buf_file)
            self.assertFalse(pub_restarted.unrecoverable_buffer_loss)
            b2 = pub_restarted.connect_and_birth("2026-06-15T08:15:30Z")
            self.assertEqual(b2[0].message_type, "NBIRTH")
            self.assertEqual(b2[0].bd_seq, 2)
            self.assertEqual(b2[0].seq, 0)
            dbirth = [e for e in b2 if e.message_type == "DBIRTH"]
            self.assertEqual(len(dbirth), 1)
            self.assertEqual(dbirth[0].tag_name, tag)
            self.assertEqual(dbirth[0].value, 75.0)
            self.assertEqual(dbirth[0].seq, 1)

            # OT-DELAY-01 visibility cutoff
            self.assertEqual(len(filter_visible_ot_events(dbirth, "2026-06-15T08:15:00Z")), 0)
            self.assertEqual(len(filter_visible_ot_events(dbirth, "2026-06-15T08:16:00Z")), 1)

            # OT-03 corrupt buffer recovery: truncated, shape-corrupt, AND non-canonical JSON surface unrecoverable_buffer_loss cleanly
            for idx, bad_json in enumerate(
                (
                    '{"bd_seq": 3, "latest_sample": ',
                    '[1, 2, 3]',
                    '{"bd_seq": 1, "latest_sample": []}',
                    '{"bd_seq": 5, "latest_sample": {"REFA.HCU.K201.SI_4110.PV": [true, "True", "2026-06-15T08:00:00Z", "x"]}}',
                )
            ):
                corrupt_file = Path(tmp) / f"corrupt_ot_buffer_{idx}.json"
                corrupt_file.write_text(bad_json, encoding="utf-8")
                pub_corrupt = SparkplugOTPublisher(schedule, buffer_path=corrupt_file)
                self.assertTrue(pub_corrupt.unrecoverable_buffer_loss)
                self.assertIn("CORRUPT_PERSISTED_BUFFER", pub_corrupt.buffer_loss_reason or "")
                b_rec = pub_corrupt.connect_and_birth("2026-06-15T08:20:00Z")
                self.assertEqual(b_rec[0].message_type, "NBIRTH")

    def test_edi_cfg0_adoption_b7_pinned_digest_persistence_prior_check_and_conflicts(self):
        cfg0_raw = json.loads(CFG0_PATH.read_text(encoding="utf-8"))

        # Canonicalization sensitivity: mutating a pump list or equipment attribute MUST change digest
        mutated_pump = json.loads(json.dumps(cfg0_raw))
        mutated_pump["piping_connections"][0]["pumps"] = []
        self.assertNotEqual(canonical_cfg0_digest(mutated_pump), PINNED_WP1B_CFG0_DIGEST)

        with tempfile.TemporaryDirectory(prefix="ppc-wp2-edi-") as tmp:
            edi_db = Path(tmp) / "edi_registry.db"
            reg1 = EDIAdoptionRegistry(db_path=edi_db)
            try:
                # EDI-001 §3: wrong expected_prior_configuration on fresh branch MUST fail closed
                with self.assertRaises(ValueError):
                    reg1.adopt_cfg0_topology(
                        CFG0_PATH,
                        request_id="REQ-CFG0-WRONG-PRIOR",
                        world_id="WORLD-PPC-V1",
                        branch_id="baseline",
                        authorized_actor="usr-ref-ops",
                        expected_cfg0_digest=PINNED_WP1B_CFG0_DIGEST,
                        expected_prior_configuration="CFG-999",
                    )

                # Valid initial adoption against independently pinned WP-1b CFG-0 digest
                r1 = reg1.adopt_cfg0_topology(
                    CFG0_PATH,
                    request_id="REQ-CFG0-001",
                    world_id="WORLD-PPC-V1",
                    branch_id="baseline",
                    authorized_actor="usr-ref-ops",
                    expected_cfg0_digest=PINNED_WP1B_CFG0_DIGEST,
                    expected_prior_configuration=None,
                    recorded_at_utc="2026-06-15T00:01:00Z",
                )
                self.assertEqual(r1["outcome"], "ADOPTED")
                self.assertTrue(r1["b7_digest_parity"])
                self.assertEqual(r1["adopted_digest"], PINNED_WP1B_CFG0_DIGEST)
                self.assertEqual(reg1.active_configuration("WORLD-PPC-V1", "baseline"), "CFG-0")
            finally:
                reg1.close()

            # Simulate FULL PROCESS RESTART opening the same SQLite registry file
            reg2 = EDIAdoptionRegistry(db_path=edi_db)
            try:
                # 1. Cross-restart replay of same request_id + same scope + same payload returns IDENTICAL receipt
                r1_replay = reg2.adopt_cfg0_topology(
                    CFG0_PATH,
                    request_id="REQ-CFG0-001",
                    world_id="WORLD-PPC-V1",
                    branch_id="baseline",
                    authorized_actor="usr-ref-ops",
                    expected_cfg0_digest=PINNED_WP1B_CFG0_DIGEST,
                    expected_prior_configuration=None,
                    recorded_at_utc="2026-06-15T00:05:00Z",
                )
                self.assertEqual(r1_replay, r1)

                # 2. Same request_id + identical payload + different world_id or branch_id -> DIFFERENT_SCOPE conflict
                scope_conflict = reg2.adopt_cfg0_topology(
                    CFG0_PATH,
                    request_id="REQ-CFG0-001",
                    world_id="WORLD-OTHER",
                    branch_id="baseline",
                    authorized_actor="usr-ref-ops",
                    expected_cfg0_digest=PINNED_WP1B_CFG0_DIGEST,
                )
                self.assertEqual(scope_conflict["outcome"], "CONFLICT")
                self.assertEqual(scope_conflict["reason"], "DIFFERENT_SCOPE_FOR_EXISTING_REQUEST_ID")

                # 3. Second distinct request on baseline with expected_prior=None now FAILS (active is CFG-0!)
                with self.assertRaises(ValueError):
                    reg2.adopt_cfg0_topology(
                        CFG0_PATH,
                        request_id="REQ-CFG0-002-STALE",
                        world_id="WORLD-PPC-V1",
                        branch_id="baseline",
                        authorized_actor="usr-ref-ops",
                        expected_cfg0_digest=PINNED_WP1B_CFG0_DIGEST,
                        expected_prior_configuration=None,
                    )

                # 4. Non-vacuous B7 digest mismatch MUST fail closed
                with self.assertRaises(ValueError):
                    reg2.adopt_cfg0_topology(
                        CFG0_PATH,
                        request_id="REQ-CFG0-BAD-DIGEST",
                        world_id="WORLD-PPC-V1",
                        branch_id="child-1",
                        authorized_actor="usr-ref-ops",
                        expected_cfg0_digest="0" * 64,
                    )

                # 5. Different payload under existing request_id -> DIFFERENT_PAYLOAD conflict
                alt = json.loads(json.dumps(cfg0_raw))
                alt["equipment"].append({"tag": "TK-EXTRA", "class": "StorageTank", "site_id": "SITE-REF-A"})
                alt_path = Path(tmp) / "alt_cfg0.json"
                alt_path.write_text(json.dumps(alt), encoding="utf-8")
                payload_conflict = reg2.adopt_cfg0_topology(
                    alt_path,
                    request_id="REQ-CFG0-001",
                    world_id="WORLD-PPC-V1",
                    branch_id="baseline",
                    authorized_actor="usr-ref-ops",
                    expected_cfg0_digest=canonical_cfg0_digest(alt),
                )
                self.assertEqual(payload_conflict["outcome"], "CONFLICT")
                self.assertEqual(payload_conflict["reason"], "DIFFERENT_PAYLOAD_FOR_EXISTING_REQUEST_ID")

                # 6. Dangling endpoint MUST fail closed
                bad = json.loads(json.dumps(cfg0_raw))
                bad["piping_connections"] = [{"id": "LINE-BAD", "from": "CDU", "to": "NONEXISTENT", "pumps": []}]
                bad_path = Path(tmp) / "bad_cfg0.json"
                bad_path.write_text(json.dumps(bad), encoding="utf-8")
                with self.assertRaises(ValueError):
                    reg2.adopt_cfg0_topology(
                        bad_path,
                        request_id="REQ-CFG0-DANGLE",
                        world_id="WORLD-PPC-V1",
                        branch_id="child-1",
                        authorized_actor="usr-ref-ops",
                        expected_cfg0_digest=canonical_cfg0_digest(bad),
                    )
            finally:
                reg2.close()

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
                    elif isinstance(node, ast.Call):
                        fn_name = (
                            node.func.id
                            if isinstance(node.func, ast.Name)
                            else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
                        )
                        if fn_name in ("__import__", "import_module"):
                            for arg in node.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    for tok in forbidden:
                                        self.assertNotIn(
                                            tok, arg.value.lower(), f"Forbidden dynamic import {arg.value} in {py_file}"
                                        )


if __name__ == "__main__":
    unittest.main()
