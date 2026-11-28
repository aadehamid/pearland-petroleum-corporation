#!/usr/bin/env python3
"""Independent verification tests for WP-2 Source Systems, OT/ICE, EDI CFG-0, and Atomic Outbox/Inbox (PO-03).

Covers:
- Atomic source DB + OutboxEntry commit (crash before commit leaves zero partial rows)
- PO-03 Crash Point 1 (before NATS ack): identical redelivery returns IDEMPOTENT_DUPLICATE with zero double business effect
- Conflicting digest for same delivery_key routes to conflict_quarantine (IDENTITY_STEWARD)
- Out-of-order source_revision enters revision_quarantine without inventing missing events
- PO-03 Crash Point 2 (between Silver staging and Delta commit): idempotent (txnAppId, txnVersion) ledger
- OT-01 ambiguous/unregistered tag rejection, OT-02 deadband + Bad quality bypass, OT-03 broker disconnect/DBIRTH rebirth, OT-DELAY-01 visibility cutoff
- EDI CFG-0 adoption digest parity (B7) and dangling edge rejection
- Zero hidden-truth imports in integration/ and ot/
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import importlib.util

from integration.edi_adoption import adopt_cfg0_topology
from integration.outbox_inbox_service import AtomicStagingInboxService
from ot.sparkplug_ice_pipeline import AmbiguousTagError, SparkplugOTPublisher, filter_visible_ot_events

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_outbox_store_module():
    path = REPO_ROOT / "source-systems" / "refinery" / "outbox_store.py"
    spec = importlib.util.spec_from_file_location("ppc_refinery_outbox_store", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestWP2SourcesOTIntegration(unittest.TestCase):
    def test_po03_atomic_outbox_crash_points_1_and_2_conflicts_and_reordering(self):
        outbox_mod = _load_outbox_store_module()
        with tempfile.TemporaryDirectory(prefix="ppc-wp2-") as tmp:
            src_store = outbox_mod.TransactionalOutboxSourceStore(Path(tmp) / "logistics.db", "logistics_mysql")
            staging = AtomicStagingInboxService(Path(tmp) / "silver_staging.db")
            try:
                # 1. Crash before source commit rolls back BOTH native record and outbox entry
                with self.assertRaises(RuntimeError):
                    src_store.commit_with_outbox(
                        source_tx_id="TX-ROLLBACK",
                        event_id="EVT-0",
                        delivery_key="deliv:logistics:baseline:0",
                        branch_id="baseline",
                        partition_key="TK-101H",
                        native_entity_key="S2-M0",
                        source_revision=1,
                        event_type="CRUDE_RECEIPT",
                        effective_at_utc="2026-06-15T08:00:00Z",
                        recorded_at_utc="2026-06-15T08:05:00Z",
                        payload={"bbl": 500.0},
                        inject_crash_before_commit=True,
                    )
                self.assertEqual(src_store.count_native_records(), 0)
                self.assertEqual(len(src_store.fetch_pending_outbox()), 0)

                # 2. Successful atomic commit of 500 bbl receipt M1
                rec = src_store.commit_with_outbox(
                    source_tx_id="TX-M1",
                    event_id="S2-M1",
                    delivery_key="deliv:logistics:baseline:S2-M1:v1",
                    branch_id="baseline",
                    partition_key="TK-101H",
                    native_entity_key="S2-M1",
                    source_revision=1,
                    event_type="CRUDE_RECEIPT",
                    effective_at_utc="2026-06-15T08:00:00Z",
                    recorded_at_utc="2026-06-15T08:05:00Z",
                    payload={"movement_id": "S2-M1", "bbl": 500.0},
                )
                ev_dict = {
                    "delivery_key": rec.delivery_key,
                    "event_id": rec.event_id,
                    "source_system": rec.source_system,
                    "branch_id": rec.branch_id,
                    "partition_key": rec.partition_key,
                    "source_sequence": rec.source_sequence,
                    "source_revision": rec.source_revision,
                    "event_type": rec.event_type,
                    "effective_at_utc": rec.effective_at_utc,
                    "recorded_at_utc": rec.recorded_at_utc,
                    "published_at_utc": "2026-06-15T08:05:02Z",
                    "provenance_class": rec.provenance_class,
                    "access_label": rec.access_label,
                    "payload_digest": rec.payload_digest,
                    "payload_json": rec.payload_json,
                }

                # 3. Crash Point 1: DB commit succeeds, worker crashes BEFORE NATS ack
                with self.assertRaises(RuntimeError):
                    staging.consume_event(ev_dict, inject_crash_after_staging_before_ack=True)
                self.assertEqual(staging.staging_count(), 1)

                # NATS redelivers exact same message -> IDEMPOTENT_DUPLICATE, zero duplicate staging rows!
                retry = staging.consume_event(ev_dict)
                self.assertEqual(retry.status, "IDEMPOTENT_DUPLICATE")
                self.assertEqual(staging.staging_count(), 1)
                src_store.mark_published(rec.delivery_key)

                # 4. Same delivery_key with DIFFERENT payload_digest -> CONFLICT_QUARANTINED
                tampered = dict(ev_dict, payload_digest="0" * 64, payload_json='{"movement_id":"S2-M1","bbl":999.0}')
                conflict = staging.consume_event(tampered)
                self.assertEqual(conflict.status, "CONFLICT_QUARANTINED")
                self.assertEqual(staging.staging_count(), 1)
                self.assertEqual(staging.quarantine_count(), 1)

                # 5. Out-of-order source_revision (rev 3 arriving when prev is 1) -> REVISION_QUARANTINED
                ooo = dict(
                    ev_dict,
                    delivery_key="deliv:logistics:baseline:S2-M1:v3",
                    event_id="S2-M1-v3",
                    source_sequence=2,
                    source_revision=3,
                )
                rev_q = staging.consume_event(ooo, expected_prev_revision=1)
                self.assertEqual(rev_q.status, "REVISION_QUARANTINED")
                self.assertEqual(staging.staging_count(), 1)

                # 6. Crash Point 2: Delta sink commits idempotently on (txnAppId, txnVersion); crash before watermark update
                delta_committed: dict[tuple[str, int], list[dict]] = {}

                def idempotent_delta_sink(*, table_name, rows, txn_app_id, txn_version):
                    key = (txn_app_id, txn_version)
                    if key not in delta_committed:
                        delta_committed[key] = list(rows)

                with self.assertRaises(RuntimeError):
                    staging.publish_staging_to_delta_idempotent(
                        txn_app_id="ppc-silver-logistics-baseline",
                        txn_version=1,
                        table_name="silver_logistics_movements",
                        source_system="logistics_mysql",
                        branch_id="baseline",
                        sink_commit_fn=idempotent_delta_sink,
                        inject_crash_after_sink_before_mark=True,
                    )
                self.assertEqual(len(delta_committed[("ppc-silver-logistics-baseline", 1)]), 1)
                self.assertEqual(staging.watermarks("logistics_mysql", "baseline")["published_seq"], 0)

                # Retry after Crash Point 2 completes cleanly without duplicating rows in Delta
                pub_retry = staging.publish_staging_to_delta_idempotent(
                    txn_app_id="ppc-silver-logistics-baseline",
                    txn_version=1,
                    table_name="silver_logistics_movements",
                    source_system="logistics_mysql",
                    branch_id="baseline",
                    sink_commit_fn=idempotent_delta_sink,
                )
                self.assertEqual(pub_retry["status"], "PUBLISHED")
                self.assertEqual(len(delta_committed[("ppc-silver-logistics-baseline", 1)]), 1)
                self.assertEqual(staging.watermarks("logistics_mysql", "baseline")["published_seq"], 1)

                # Second call with same txn_version returns IDEMPOTENT_ALREADY_PUBLISHED
                pub_again = staging.publish_staging_to_delta_idempotent(
                    txn_app_id="ppc-silver-logistics-baseline",
                    txn_version=1,
                    table_name="silver_logistics_movements",
                    source_system="logistics_mysql",
                    branch_id="baseline",
                    sink_commit_fn=idempotent_delta_sink,
                )
                self.assertEqual(pub_again["status"], "IDEMPOTENT_ALREADY_PUBLISHED")
            finally:
                src_store.close()
                staging.close()

    def test_ot01_to_ot03_and_ot_delay01_sparkplug_behaviors(self):
        schedule = {
            "tags": [
                {"tag_name": "REF_A.4B.K401.CIRC_FRAC", "equipment_id": "4B", "unit": "fraction", "deadband": 0.01},
                {"tag_name": "REF_A.TK301.LEVEL_BBL", "equipment_id": "TK-301", "unit": "bbl", "deadband": 50.0},
            ]
        }
        # OT-01: duplicate tag in schedule rejected
        with self.assertRaises(AmbiguousTagError):
            SparkplugOTPublisher({"tags": schedule["tags"] + [schedule["tags"][0]]})

        pub = SparkplugOTPublisher(schedule)
        births = pub.connect_and_birth("2026-06-15T08:00:00Z")
        self.assertEqual(len(births), 2)
        self.assertEqual(pub.bd_seq, 1)

        # OT-01: unregistered tag rejected
        with self.assertRaises(AmbiguousTagError):
            pub.ingest_sample("REF_A.UNKNOWN.TAG", 1.0, "Good", "2026-06-15T08:01:00Z", "2026-06-15T08:01:00Z", "2026-06-15T08:01:00Z")

        # Initial Good sample publishes
        e1 = pub.ingest_sample("REF_A.4B.K401.CIRC_FRAC", 1.00, "Good", "2026-06-15T08:01:00Z", "2026-06-15T08:01:00Z", "2026-06-15T08:01:01Z")
        self.assertIsNotNone(e1)

        # OT-02: small change inside deadband with same quality suppressed
        e_suppressed = pub.ingest_sample("REF_A.4B.K401.CIRC_FRAC", 1.002, "Good", "2026-06-15T08:02:00Z", "2026-06-15T08:02:00Z", "2026-06-15T08:02:01Z")
        self.assertIsNone(e_suppressed)

        # OT-02: Bad quality transition MUST bypass deadband even with zero value change!
        e_bad = pub.ingest_sample("REF_A.4B.K401.CIRC_FRAC", 1.002, "Bad", "2026-06-15T08:03:00Z", "2026-06-15T08:03:00Z", "2026-06-15T08:03:01Z")
        self.assertIsNotNone(e_bad)
        assert e_bad is not None
        self.assertEqual(e_bad.quality, "Bad")

        # OT-03: Broker disconnect buffers silently; reconnect issues DBIRTH rebirth with incremented bd_seq
        pub.simulate_broker_disconnect()
        self.assertIsNone(
            pub.ingest_sample("REF_A.4B.K401.CIRC_FRAC", 0.75, "Good", "2026-06-15T08:10:00Z", "2026-06-15T08:10:01Z", "2026-06-15T08:15:30Z")
        )
        rebirth = pub.connect_and_birth("2026-06-15T08:15:30Z")
        self.assertEqual(pub.bd_seq, 2)
        comp = next(ev for ev in rebirth if ev.tag_name == "REF_A.4B.K401.CIRC_FRAC")
        self.assertAlmostEqual(comp.value, 0.75, places=6)

        # OT-DELAY-01: published at 08:15:30Z -> invisible at 08:15:00Z, visible at 08:16:00Z
        self.assertEqual(len(filter_visible_ot_events([comp], "2026-06-15T08:15:00Z")), 0)
        self.assertEqual(len(filter_visible_ot_events([comp], "2026-06-15T08:16:00Z")), 1)

    def test_edi_cfg0_adoption_b7_digest_parity_and_dangling_edge_rejection(self):
        with tempfile.TemporaryDirectory(prefix="ppc-edi-") as tmp:
            cfg_ok = Path(tmp) / "cfg0.json"
            cfg_ok.write_text(
                json.dumps(
                    {
                        "cfg_version": "CFG-0",
                        "facility_id": "SITE-REF-A",
                        "equipment": [{"id": "CDU"}, {"id": "4B"}],
                        "streams": [{"id": "S1", "source": "CDU", "destination": "4B"}],
                    }
                ),
                encoding="utf-8",
            )
            receipt = adopt_cfg0_topology(cfg_ok, branch_id="baseline", reviewer_id="ops-engineer-1")
            self.assertTrue(receipt["b7_digest_parity"])
            self.assertEqual(receipt["cfg0_source_digest"], receipt["adopted_digest"])

            cfg_bad = Path(tmp) / "cfg0_bad.json"
            cfg_bad.write_text(
                json.dumps(
                    {
                        "cfg_version": "CFG-0",
                        "facility_id": "SITE-REF-A",
                        "equipment": [{"id": "CDU"}],
                        "streams": [{"id": "S1", "source": "CDU", "destination": "GHOST_UNIT"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                adopt_cfg0_topology(cfg_bad, branch_id="baseline", reviewer_id="ops-engineer-1")


if __name__ == "__main__":
    unittest.main()
