"""WP-0 contract, schema, adapter, semantic, and infrastructure verification tests.

Runs completely offline with zero network calls or secrets required.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

import jsonschema
import pyshacl
import rdflib
import yaml
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
ADAPTERS_DIR = REPO_ROOT / "semantic" / "adapters"
INFRA_DIR = REPO_ROOT / "infra"
FIXTURES_DIR = REPO_ROOT / "fixtures" / "golden"

SHA = "a" * 64
SHA_B = "b" * 64
TS = "2026-11-27T10:00:00Z"
TS_LATER = "2026-11-27T10:30:00Z"

REQUIRED_SCHEMAS = {
    "release_manifest.schema.json",
    "world_export_bundle.schema.json",
    "source_event.schema.json",
    "outbox_entry.schema.json",
    "inbox_receipt.schema.json",
    "model_run.schema.json",
    "tool_request.schema.json",
    "tool_response.schema.json",
    "action_proposal.schema.json",
    "action_authorization.schema.json",
    "action_receipt.schema.json",
    "scenario_case.schema.json",
    "provisional_adapter_manifest.schema.json",
}


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def validate_payload(schema_name: str, payload: dict) -> None:
    schema = load_schema(schema_name)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)


def valid_payloads() -> dict[str, dict]:
    return {
        "release_manifest.schema.json": {
            "schema_version": "1.0.0",
            "release_id": "REL-20261127-001",
            "publication_id": "PUB-REL-001",
            "subject_scope": "baseline/site:SITE-REF-A/kpi_store",
            "scoped_ordinal": 1,
            "supersedes_release_id": None,
            "branch_id": "baseline",
            "world_version": "world-v1.0.0",
            "epm_release_id": "epm-provisional-511a9e8d",
            "status": "PUBLISHED",
            "source_recorded_at": TS,
            "published_at": TS,
            "authorization_label": "OPERATIONS",
            "access_scope": "OPERATIONS",
            "provenance_class": "DERIVED",
            "availability_receipts": [
                {
                    "receipt_id": "REC-001",
                    "recipient_role": "Planner",
                    "channel": "workspace",
                    "available_at": TS_LATER,
                }
            ],
            "table_snapshots": [
                {
                    "table_name": "gold_kpi_facts",
                    "delta_version": 0,
                    "r2_uri": "s3://pearland-petroleum-corp/delta/kpi_store/gold_kpi_facts",
                    "snapshot_sha256": SHA,
                }
            ],
            "source_watermarks": [
                {
                    "source_system": "commercial_ctrm",
                    "captured_seq": 10,
                    "durable_seq": 10,
                    "applied_seq": 10,
                    "published_seq": 10,
                    "complete": True,
                }
            ],
            "semantic_digests": {"ppc_core.ttl": SHA},
            "mapping_digests": {"epm.adapter.json": SHA_B},
            "model_version": "refinery-a-v1.0.0",
            "reconciliation_report": {
                "status": "PASSED",
                "report_ref": "manifests/releases/REL-20261127-001-recon.json",
                "report_sha256": SHA,
            },
            "approval_evidence": {
                "status": "QUALIFIED_PROVISIONAL",
                "evidence_ref": "fixtures/golden/wp0_probe_evidence.json",
                "approved_by": "aadehamid",
                "approved_at": TS_LATER,
            },
        },
        "world_export_bundle.schema.json": {
            "schema_version": "1.0.0",
            "bundle_id": "WEB-V1-001",
            "bundle_version": "1.0.0",
            "world_version": "world-v1.0.0",
            "branch_id": "baseline",
            "seed_policy": {
                "prng_algorithm": "numpy.random.PCG64",
                "prng_version": "numpy==2.2.6",
                "root_seed": 20261127,
            },
            "created_at": TS,
            "qualification_verdict": "QUALIFIED_PROVISIONAL",
            "provenance_class": "SYNTHETIC",
            "upstream_adapter_pins": [
                {"upstream_repo": "aadehamid/enterprise-performance-model", "pinned_commit": "511a9e8d", "adapter_version": "0.1.0", "maturity_status": "PROVISIONAL_COMMIT_PIN"},
                {"upstream_repo": "aadehamid/industrial-context-engineering", "pinned_commit": "1467e92", "adapter_version": "0.1.0", "maturity_status": "PROVISIONAL_COMMIT_PIN"},
                {"upstream_repo": "aadehamid/engineering-drawing-intelligence", "pinned_commit": "12a4a6a", "adapter_version": "0.1.0", "maturity_status": "PROVISIONAL_COMMIT_PIN"},
                {"upstream_repo": "aadehamid/enterprise-context-engineering", "pinned_commit": "750b398", "adapter_version": "0.1.0", "maturity_status": "PROVISIONAL_COMMIT_PIN"},
            ],
            "observable": {
                "r2_bucket": "pearland-petroleum-corp",
                "r2_prefix": "exports/world_bundle/observable/v1.0.0/",
                "delta_tables": [{"name": "gold_kpi_facts", "path": "delta/kpi_store/gold_kpi_facts", "sha256": SHA, "size_bytes": 1024}],
                "ice_ot_l0": [{"name": "refinery_a_ot_tags", "path": "ot/tags.parquet", "sha256": SHA, "size_bytes": 512}],
                "edi_topology": [{"name": "cfg0_dexpi", "path": "edi/cfg0.json", "sha256": SHA, "size_bytes": 256}],
                "epm_kpi_fixtures": [{"name": "kpi_tall", "path": "epm/kpi.parquet", "sha256": SHA, "size_bytes": 512}],
                "ece_evidence_dossiers": [{"name": "dossiers", "path": "ece/dossiers.jsonl", "sha256": SHA, "size_bytes": 512}],
            },
            "hidden_truth": {
                "r2_bucket": "pearland-petroleum-hidden",
                "r2_prefix": "evaluation/hidden/world_bundle/v1.0.0/",
                "separate_credential_boundary": True,
                "canonical_world_snapshots": [{"name": "world_ckpt_0", "path": "evaluation/hidden/world_version=v1/ckpt0.json", "sha256": SHA_B, "size_bytes": 4096}],
                "evaluation_scoring_keys": [{"name": "scoring_keys", "path": "evaluation/hidden/scoring_keys/v1.json", "sha256": SHA_B, "size_bytes": 1024}],
            },
            "leak_audit": {
                "status": "PASSED",
                "checked_at": TS_LATER,
                "hidden_fields_found_in_observable": 0,
                "audit_sha256": SHA,
            },
        },
        "source_event.schema.json": {
            "schema_version": "1.0.0",
            "publication_id": "S2-P1",
            "subject_scope": "baseline/lot:LOT-44/lims",
            "scoped_ordinal": 1,
            "supersedes_publication_id": None,
            "event_id": "EVT-LIMS-001",
            "source_system": "refinery_lims",
            "source_incarnation": "lims-site-a-01",
            "native_entity_key": "LOT-44",
            "source_revision": 1,
            "event_type": "ASSAY_FAILED_QUALITY_HOLD",
            "effective_at": TS,
            "recorded_at": TS,
            "published_at": TS,
            "branch_id": "baseline",
            "partition_key": "LOT-44",
            "source_sequence": 1,
            "provenance_class": "SYNTHETIC",
            "access_label": "OPERATIONS",
            "availability_receipts": [
                {"receipt_id": "S2-R1", "recipient_role": "Planner", "channel": "workspace", "available_at": TS_LATER}
            ],
            "payload_ref": "raw/source_extracts/sqlite/EVT-LIMS-001.json",
            "payload_digest": SHA,
            "producer_identity": "svc-refinery-lims",
            "delivery_key": "lims:LOT-44:v1",
            "predecessor_event_id": None,
            "correlation_id": "CORR-S2-001",
        },
        "outbox_entry.schema.json": {
            "schema_version": "1.0.0",
            "outbox_id": "OBX-001",
            "source_system": "logistics_mysql",
            "source_transaction_id": "MYSQL-TXN-991",
            "event_id": "EVT-MOV-01",
            "delivery_key": "log:S2-M1:v1",
            "branch_id": "baseline",
            "source_sequence": 1,
            "payload_digest": SHA,
            "publish_status": "PENDING",
            "created_at": TS,
            "published_at": None,
            "attempt_count": 0,
        },
        "inbox_receipt.schema.json": {
            "schema_version": "1.0.0",
            "receipt_id": "INB-001",
            "delivery_key": "log:S2-M1:v1",
            "source_system": "logistics_mysql",
            "source_sequence": 1,
            "source_revision": 1,
            "payload_digest": SHA,
            "processing_status": "APPLIED",
            "applied_result": "STAGED_MOVEMENT_500_BBL",
            "branch_id": "baseline",
            "acknowledged_at": TS_LATER,
            "delta_txn_app_id": "ppc-silver-logistics",
            "delta_txn_version": 1,
        },
        "model_run.schema.json": {
            "schema_version": "1.0.0",
            "run_id": "MR-LP-001",
            "method_class": "PLANNING_LP",
            "model_digest": SHA,
            "formula_digest": SHA,
            "parameter_digest": SHA_B,
            "branch_id": "scn-a-derate",
            "subject_scope": "SITE-REF-A/HCU",
            "actor_id": "usr-planner-01",
            "actor_role": "Planner",
            "channel": "workspace",
            "purpose": "derate-response",
            "access_scope": "OPERATIONS",
            "effective_at": TS,
            "knowledge_cutoff": TS,
            "world_version": "world-v1.0.0",
            "product_release_id": "REL-20261127-001",
            "horizon": "6h",
            "grain": "1h",
            "units": "bbl/day",
            "measurement_basis": "bbl_60F",
            "input_digest": SHA,
            "input_provenance": ["SYNTHETIC", "SCENARIO_ASSUMPTION"],
            "output_provenance_class": "ESTIMATED",
            "epistemic_status": "INFERENCE",
            "lifecycle_status": "RELEASED",
            "released_at": TS_LATER,
            "seed": 42,
            "solver_configuration": {
                "solver_name": "HiGHS",
                "solver_version": "1.8.0",
                "feasibility_tolerance": 1e-7,
            },
            "feasibility_status": "FEASIBLE",
            "binding_constraints": ["HCU_RECYCLE_COMPRESSOR_CIRC_CAP_30000_BPD"],
            "uncertainty_representation": {"kind": "DETERMINISTIC"},
            "output_digest": SHA_B,
        },
        "tool_request.schema.json": {
            "schema_version": "1.0.0",
            "request_id": "TREQ-001",
            "subject_scope": "SITE-REF-A/TERM-01",
            "effective_at": TS,
            "actor_id": "usr-planner-01",
            "delegated_role": "Planner",
            "channel": "workspace",
            "purpose": "derate-response",
            "tool_name": "simulate_terminal_transfer",
            "contract_version": "1.0.0",
            "branch_id": "scn-a-derate",
            "pinned_release_ids": ["REL-20261127-001"],
            "knowledge_cutoff": TS,
            "input_digest": SHA,
            "requested_action": "simulate_inter_terminal_transfer",
            "expires_at": TS_LATER,
        },
        "tool_response.schema.json": {
            "schema_version": "1.0.0",
            "result_id": "TRES-001",
            "request_id": "TREQ-001",
            "status": "OK",
            "branch_id": "scn-a-derate",
            "knowledge_cutoff": TS,
            "provenance_class": "ESTIMATED",
            "epistemic_status": "INFERENCE",
            "output_classification": "OPERATIONS",
            "source_or_model_refs": ["MR-LP-001"],
            "uncertainty": {"kind": "INTERVAL", "summary": "+/- 250 bbl"},
            "redaction_status": "NONE",
            "audit_id": "AUD-001",
            "payload": {"transfer_bbl": 5000},
        },
        "action_proposal.schema.json": {
            "schema_version": "1.0.0",
            "proposal_id": "PROP-001",
            "decision_id": "DEC-001",
            "payload_digest": SHA,
            "status": "RECOMMENDED",
            "authority_class": "REQUIRE_APPROVAL",
            "approval_tier": 2,
            "proposing_actor_id": "agent-ops-01",
            "knowledge_cutoff": TS,
            "measurement_basis": "bbl_60F",
            "action_type": "inter_terminal_transfer",
            "target_id": "TERM-01",
            "quantity": 5000,
            "unit": "bbl_60F",
            "estimated_margin_effect_usd": 45000,
            "estimated_notional_usd": 525000,
            "model_run_id": "MR-LP-001",
            "branch_id": "scn-a-derate",
            "expected_source_revisions": {"logistics_mysql": "rev-14"},
            "policy_version": "1.0.0",
            "approver_role": "Commercial Manager",
            "evidence_release_id": "REL-20261127-001",
            "expires_at": TS_LATER,
            "idempotency_key": "idem-prop-001",
            "provenance_class": "SCENARIO_ASSUMPTION",
        },
        "action_authorization.schema.json": {
            "schema_version": "1.0.0",
            "authorization_id": "AUTH-001",
            "authorized_at": TS,
            "proposal_id": "PROP-001",
            "proposal_payload_digest": SHA,
            "branch_id": "scn-a-derate",
            "authorization_expiry": TS_LATER,
            "approver_actor_id": "usr-comm-mgr-01",
            "approver_role": "Commercial Manager",
            "approver_is_human": True,
            "scope": "SITE-REF-A/TERM-01",
            "policy_version": "1.0.0",
            "policy_check_id": "PCHK-001",
            "decision": "APPROVED",
            "denial_reason": None,
            "audit_evidence": {
                "signature_kind": "PG_TXN_AUDIT",
                "signature_digest": SHA_B,
                "session_id": "sess-001",
            },
        },
        "action_receipt.schema.json": {
            "schema_version": "1.0.0",
            "receipt_id": "AREC-001",
            "proposal_id": "PROP-001",
            "authorization_basis_kind": "HUMAN_AUTHORIZATION",
            "authorization_basis_id": "AUTH-001",
            "idempotency_key": "idem-prop-001",
            "source_revisions": {"logistics_mysql": "rev-14"},
            "execution_status": "EXECUTED",
            "executed_at": TS_LATER,
            "business_effect_id": "XFER-5000-001",
            "blocked_reason": None,
            "branch_id": "scn-a-derate",
        },
        "scenario_case.schema.json": {
            "schema_version": "1.0.0",
            "case_id": "SCN-A-T125",
            "case_version": "1.0.0",
            "use_case_ids": ["UC-1", "UC-3"],
            "lifecycle_status": "DRAFT",
            "world_version": "world-v1.0.0",
            "branch_id": "scn-a-t125",
            "parent_checkpoint_id": "CKPT-0800",
            "logical_clock": {
                "origin_utc": TS,
                "horizon_end_utc": TS_LATER,
                "process_step_seconds": 60,
                "site_timezone": "America/Chicago",
            },
            "public_source_vintage": "eia-2026-11-20",
            "model_pin": {
                "model_release_id": "refinery-a-v1.0.0",
                "equation_set_version": "EQ-01..09-v1.2.0",
            },
            "upstream_contract_pins": {
                "epm": "511a9e8db4008ef43a0dda0f92cef17664e4c995",
                "ice": "1467e9278a9fa50d80618a296297eb40cd4416c2",
                "edi": "12a4a6a6f715c7db76a26d763cb1938d6cf0cc05",
                "ece": "750b398b6a50aedd552a72056d09cf1ccf6a296a",
            },
            "evidence_cutoff": TS_LATER,
            "query_channel": "workspace",
            "query_purpose": "derate-response",
            "allowed_roles": ["Planner", "Commercial Manager"],
            "expected_source_records": ["OT-HCU-COMP-0810"],
            "failure_injections": ["ambiguous_tag", "duplicate_retry_crash_1"],
            "interventions": [
                {
                    "intervention_id": "INT-COMP-75PCT",
                    "effective_at": TS,
                    "description": "Reduce HCU recycle compressor circulation to 75%",
                    "provenance_class": "SCENARIO_ASSUMPTION",
                }
            ],
            "expected_release_ids": ["REL-SCN-A-001"],
            "oracle_version": "oracle-v1.0.0",
            "access_policy": "OPERATIONS",
            "provenance_class": "SCENARIO_ASSUMPTION",
        },
        "provisional_adapter_manifest.schema.json": json.loads(
            (ADAPTERS_DIR / "epm.adapter.json").read_text(encoding="utf-8")
        ),
    }


class TestWP0Schemas(unittest.TestCase):
    def test_exact_thirteen_schemas_exist_and_are_valid_draft_2020_12(self):
        actual = {p.name for p in SCHEMAS_DIR.glob("*.schema.json")}
        self.assertEqual(actual, REQUIRED_SCHEMAS)
        for name in sorted(REQUIRED_SCHEMAS):
            Draft202012Validator.check_schema(load_schema(name))

    def test_valid_and_invalid_payloads_for_every_schema(self):
        payloads = valid_payloads()
        self.assertEqual(set(payloads.keys()), REQUIRED_SCHEMAS)
        for name, valid in payloads.items():
            with self.subTest(schema=name, case="valid"):
                validate_payload(name, valid)

            with self.subTest(schema=name, case="reject_unknown_field"):
                bad = copy.deepcopy(valid)
                bad["unexpected_extra_field"] = "forbidden"
                with self.assertRaises(jsonschema.ValidationError):
                    validate_payload(name, bad)

            with self.subTest(schema=name, case="reject_missing_schema_version"):
                bad = copy.deepcopy(valid)
                del bad["schema_version"]
                with self.assertRaises(jsonschema.ValidationError):
                    validate_payload(name, bad)

    def test_domain_specific_schema_invariants(self):
        payloads = valid_payloads()

        # UNRESOLVED ToolResponse must not disclose refs or payload
        unresolved_leak = copy.deepcopy(payloads["tool_response.schema.json"])
        unresolved_leak["status"] = "UNRESOLVED"
        unresolved_leak["redaction_status"] = "NONDISCLOSING_UNRESOLVED"
        unresolved_leak["payload"] = None
        unresolved_leak["source_or_model_refs"] = ["SECRET-REF-1"]
        with self.assertRaises(jsonschema.ValidationError):
            validate_payload("tool_response.schema.json", unresolved_leak)

        unresolved_ok = copy.deepcopy(unresolved_leak)
        unresolved_ok["source_or_model_refs"] = []
        validate_payload("tool_response.schema.json", unresolved_ok)

        # Agent can never approve an ActionAuthorization
        agent_auth = copy.deepcopy(payloads["action_authorization.schema.json"])
        agent_auth["approver_is_human"] = False
        with self.assertRaises(jsonschema.ValidationError):
            validate_payload("action_authorization.schema.json", agent_auth)

        # EXECUTED ActionReceipt must carry business_effect_id and null blocked_reason
        bad_receipt = copy.deepcopy(payloads["action_receipt.schema.json"])
        bad_receipt["business_effect_id"] = None
        with self.assertRaises(jsonschema.ValidationError):
            validate_payload("action_receipt.schema.json", bad_receipt)

        # WorldExportBundle must enforce separate credential boundary and forbid hidden bucket in observable
        bad_bundle = copy.deepcopy(payloads["world_export_bundle.schema.json"])
        bad_bundle["hidden_truth"]["separate_credential_boundary"] = False
        with self.assertRaises(jsonschema.ValidationError):
            validate_payload("world_export_bundle.schema.json", bad_bundle)

        bad_bundle2 = copy.deepcopy(payloads["world_export_bundle.schema.json"])
        bad_bundle2["observable"]["r2_bucket"] = "pearland-petroleum-hidden"
        with self.assertRaises(jsonschema.ValidationError):
            validate_payload("world_export_bundle.schema.json", bad_bundle2)

        # Provisional adapter cannot claim an approved release or QUALIFIED cap
        bad_adapter = copy.deepcopy(payloads["provisional_adapter_manifest.schema.json"])
        bad_adapter["approved_upstream_release"] = "1.0.0"
        with self.assertRaises(jsonschema.ValidationError):
            validate_payload("provisional_adapter_manifest.schema.json", bad_adapter)

        # Approved upstream release cannot leave approved_upstream_release null or cap provisional
        bad_approved = copy.deepcopy(payloads["provisional_adapter_manifest.schema.json"])
        bad_approved["maturity_status"] = "APPROVED_UPSTREAM_RELEASE"
        bad_approved["approved_upstream_release"] = None
        bad_approved["qualification_cap"] = "QUALIFIED"
        with self.assertRaises(jsonschema.ValidationError):
            validate_payload("provisional_adapter_manifest.schema.json", bad_approved)

        # PROHIBITED ActionProposal cannot be APPROVED, EXECUTED, or AUTO_EXECUTED (ADR-0056 G3-b)
        for bad_status in ("APPROVED", "EXECUTED", "AUTO_EXECUTED"):
            bad_prop = copy.deepcopy(payloads["action_proposal.schema.json"])
            bad_prop["authority_class"] = "PROHIBITED"
            bad_prop["status"] = bad_status
            with self.assertRaises(jsonschema.ValidationError):
                validate_payload("action_proposal.schema.json", bad_prop)

        # ReleaseManifest table snapshots cannot point to hidden bucket (ADR-0053, ADR-0057)
        bad_rm = copy.deepcopy(payloads["release_manifest.schema.json"])
        bad_rm["table_snapshots"][0]["r2_uri"] = "s3://pearland-petroleum-hidden/delta/kpi_store/gold_kpi_facts"
        with self.assertRaises(jsonschema.ValidationError):
            validate_payload("release_manifest.schema.json", bad_rm)


class TestWP0PolicyAndPins(unittest.TestCase):
    def test_policy_thresholds_match_adr_0056(self):
        policy = yaml.safe_load((SCHEMAS_DIR / "policy_thresholds.yaml").read_text(encoding="utf-8"))
        self.assertTrue(policy["global_invariants"]["proposer_cannot_approve"])
        self.assertTrue(policy["global_invariants"]["agent_cannot_approve"])
        self.assertEqual(policy["global_invariants"]["identity_steward_role"], "IDENTITY_STEWARD")

        auto = policy["authority_classes"]["AUTO_EXECUTE"]
        self.assertEqual(auto["preapproval_grant_id"], "PG-A0-v1")
        self.assertEqual(auto["limits"]["max_volume_bbl_60f"], 0)
        self.assertEqual(auto["limits"]["max_margin_effect_usd"], 0)
        self.assertEqual(auto["limits"]["max_executions_per_agent_per_logical_hour"], 20)

        t1 = policy["authority_classes"]["REQUIRE_APPROVAL_TIER_1"]
        self.assertEqual(t1["limits"]["max_rate_change_pct"], 10.0)
        self.assertEqual(t1["limits"]["max_rate_change_bbl_per_day"], 4000)
        self.assertEqual(t1["limits"]["max_cut_point_shift_c"], 5.0)
        self.assertEqual(t1["limits"]["max_transfer_volume_bbl_60f"], 25000)
        self.assertEqual(t1["limits"]["max_margin_effect_usd"], 250000)
        self.assertEqual(t1["approver_roles"]["default"], "Shift Supervisor")
        self.assertEqual(t1["expiry_logical_minutes"], 30)

        t2 = policy["authority_classes"]["REQUIRE_APPROVAL_TIER_2"]
        self.assertEqual(t2["limits"]["max_cut_point_shift_c"], 15.0)
        self.assertEqual(t2["limits"]["max_volume_bbl_60f"], 50000)
        self.assertEqual(t2["limits"]["max_notional_usd"], 5000000)
        self.assertEqual(t2["limits"]["max_margin_effect_usd"], 1000000)
        self.assertEqual(t2["limits"]["max_delivery_reschedule_hours"], 72)
        self.assertEqual(t2["expiry_logical_minutes"], 240)

        prohibited = policy["authority_classes"]["PROHIBITED"]
        self.assertEqual(prohibited["policy_result"], "DENIED")
        self.assertFalse(prohibited["agent_path_allowed"])
        self.assertIn("read_or_write_evaluation_hidden", prohibited["prohibited_actions"])
        self.assertIn("release_lot_from_quality_hold", prohibited["prohibited_actions"])

    def test_provisional_adapter_manifests_pin_exact_commits_with_zero_invented_approvals(self):
        expected = {
            "epm.adapter.json": ("EPM", "511a9e8db4008ef43a0dda0f92cef17664e4c995"),
            "ice.adapter.json": ("ICE", "1467e9278a9fa50d80618a296297eb40cd4416c2"),
            "edi.adapter.json": ("EDI", "12a4a6a6f715c7db76a26d763cb1938d6cf0cc05"),
            "ece.adapter.json": ("ECE", "750b398b6a50aedd552a72056d09cf1ccf6a296a"),
        }
        actual_files = {p.name for p in ADAPTERS_DIR.glob("*.adapter.json")}
        self.assertEqual(actual_files, set(expected.keys()))
        for fname, (short_name, commit) in expected.items():
            data = json.loads((ADAPTERS_DIR / fname).read_text(encoding="utf-8"))
            validate_payload("provisional_adapter_manifest.schema.json", data)
            self.assertEqual(data["upstream_short_name"], short_name)
            self.assertEqual(data["pinned_commit"], commit)
            self.assertEqual(data["maturity_status"], "PROVISIONAL_COMMIT_PIN")
            self.assertIsNone(data["approved_upstream_release"])
            self.assertEqual(data["qualification_cap"], "QUALIFIED_PROVISIONAL")

    def test_runtime_freeze_pins_required_parameters(self):
        rf = yaml.safe_load((SCHEMAS_DIR / "runtime_freeze.yaml").read_text(encoding="utf-8"))
        self.assertEqual(rf["prng"]["bit_generator"], "PCG64")
        self.assertEqual(rf["clock_and_calendar"]["site_timezone"], "America/Chicago")
        self.assertEqual(rf["clock_and_calendar"]["business_day_start_hour_local"], 6)
        self.assertEqual(rf["clock_and_calendar"]["hybrid_clock"]["canonical_process_step_seconds"], 60)
        self.assertEqual(rf["analytical_release_cadence"]["delta_write_policy"]["aws_conditional_put"], "etag")
        self.assertEqual(rf["analytical_release_cadence"]["delta_write_policy"]["dagster_concurrency_pool_per_table"], 1)
        self.assertEqual(rf["analytical_release_cadence"]["delta_write_policy"]["duckdb_access_mode"], "read_only")


class TestWP0SemanticAndInfra(unittest.TestCase):
    def test_turtle_and_shacl_conform_and_reject_invalid_provenance(self):
        data_graph = rdflib.Graph().parse(REPO_ROOT / "semantic" / "ontology" / "ppc_core.ttl", format="turtle")
        shapes_graph = rdflib.Graph().parse(REPO_ROOT / "semantic" / "shapes" / "ppc_core.shacl.ttl", format="turtle")
        conforms, _, report = pyshacl.validate(data_graph, shacl_graph=shapes_graph)
        self.assertTrue(conforms, report)

        # Negative test: invalid provenanceClass must fail SHACL validation
        bad_ttl = (REPO_ROOT / "semantic" / "ontology" / "ppc_core.ttl").read_text(encoding="utf-8").replace(
            'ppc:provenanceClass "SYNTHETIC"', 'ppc:provenanceClass "UNCLASSIFIED"'
        )
        bad_graph = rdflib.Graph().parse(data=bad_ttl, format="turtle")
        bad_conforms, _, _ = pyshacl.validate(bad_graph, shacl_graph=shapes_graph)
        self.assertFalse(bad_conforms)

    def test_aml_core_model_declares_governed_entities(self):
        aml = (REPO_ROOT / "semantic" / "aml" / "ppc_core.aml").read_text(encoding="utf-8")
        for entity in (
            "refinery_site",
            "storage_tank",
            "source_event",
            "outbox_entry",
            "inbox_receipt",
            "release_manifest",
            "kpi_value_record",
            "model_run",
            "action_proposal",
            "action_authorization",
            "action_receipt",
            "users",
            "role_assignments",
        ):
            self.assertRegex(aml, rf"(?m)^{entity}\s*\{{")

    def test_r2_prefix_map_and_legacy_inventory_integrity(self):
        pmap = yaml.safe_load((INFRA_DIR / "r2" / "r2_prefix_map.yaml").read_text(encoding="utf-8"))
        self.assertEqual(pmap["buckets"]["operational"]["bucket_name"], "pearland-petroleum-corp")
        self.assertEqual(pmap["buckets"]["hidden_truth"]["bucket_name"], "pearland-petroleum-hidden")

        inv_path = INFRA_DIR / "r2" / "legacy_pre_world_model_inventory.json"
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        recorded_sha = inv.pop("inventory_sha256")
        computed_sha = hashlib.sha256(json.dumps(inv, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(recorded_sha, computed_sha)
        self.assertEqual(inv["quarantine_label"], "LEGACY_PRE_WORLD_MODEL")
        self.assertEqual(inv["buckets"][0]["object_count"], 18)
        self.assertEqual(inv["buckets"][0]["total_bytes"], 2744948808)

    def test_probe_evidence_integrity_and_no_leaked_secrets(self):
        ev_path = FIXTURES_DIR / "wp0_probe_evidence.json"
        raw_text = ev_path.read_text(encoding="utf-8")
        # Guard against accidentally committing access keys or Databricks tokens
        self.assertNotRegex(raw_text, r"dapi[0-9a-f]{16,}")
        self.assertNotIn("SECRET_ACCESS_KEY", raw_text)

        ev = json.loads(raw_text)
        recorded_sha = ev.pop("evidence_sha256")
        computed_sha = hashlib.sha256(json.dumps(ev, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(recorded_sha, computed_sha)
        self.assertEqual(ev["r2_two_bucket_isolation"]["status"], "PASSED")
        self.assertEqual(ev["delta_rs_r2_and_duckdb"]["aws_conditional_put"], "etag")
        self.assertEqual(ev["delta_rs_r2_and_duckdb"]["etag_if_none_match_conflict"]["http_status"], 412)
        self.assertTrue(ev["delta_rs_r2_and_duckdb"]["duckdb_readonly_initial_parity"])
        self.assertEqual(ev["databricks_free_edition_sync"]["status"], "PASSED")
        self.assertTrue(ev["databricks_free_edition_sync"]["duckdb_to_databricks_row_parity"])

    def test_docker_compose_enforces_adr_0055_layout_and_12gb_budget(self):
        compose = yaml.safe_load((INFRA_DIR / "docker-compose.yml").read_text(encoding="utf-8"))
        services = compose["services"]
        expected_services = {"postgres", "mysql", "neo4j", "nats", "mosquitto", "otel-collector"}
        self.assertEqual(set(services.keys()), expected_services)
        # ADR-0055: no Langfuse v3 / ClickHouse / Ollama / Cloudflare D1 services in Slice 1
        services_blob = json.dumps(services).lower()
        for forbidden in ("clickhouse", "langfuse", "ollama", "wrangler", "cloudflare-d1"):
            self.assertNotIn(forbidden, services_blob)

        total_mb = 0
        for svc in services.values():
            mem = str(svc["mem_limit"]).lower()
            m = re.fullmatch(r"(\d+)m", mem)
            self.assertIsNotNone(m, f"Expected MB mem_limit, got {mem}")
            total_mb += int(m.group(1))
        # Stores + OTel collector must leave comfortable RAM for Dagster/FastAPI/Dash + OS in 12 GB VM
        self.assertLessEqual(total_mb, 8192)

        dagster_cfg = yaml.safe_load((INFRA_DIR / "dagster" / "dagster.yaml").read_text(encoding="utf-8"))
        limits = dagster_cfg["run_coordinator"]["config"]["tag_concurrency_limits"]
        self.assertIn(
            {"key": "ppc/delta_table", "value": {"applyLimitPerUniqueValue": True}, "limit": 1},
            limits,
        )

    def test_probe_helper_guards_offline(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("wp0_probes", REPO_ROOT / "lakehouse" / "delta" / "wp0_probes.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        opts = mod.r2_storage_options(
            {
                "R2_ACCESS_KEY_ID": "test-key",
                "R2_SECRET_ACCESS_KEY": "test-secret",
                "R2_ENDPOINT": "https://example.r2.cloudflarestorage.com",
            }
        )
        self.assertEqual(opts["aws_conditional_put"], "etag")
        self.assertEqual(opts["AWS_ALLOW_HTTP"], "false")

        with self.assertRaises(ValueError):
            mod.delete_r2_prefix(None, "pearland-petroleum-corp", "delta/silver/")

        # Run-level Dagster tag helper must match infra/dagster/dagster.yaml key verbatim
        dagster_cfg = yaml.safe_load((INFRA_DIR / "dagster" / "dagster.yaml").read_text(encoding="utf-8"))
        configured_keys = {
            entry["key"]
            for entry in dagster_cfg["run_coordinator"]["config"]["tag_concurrency_limits"]
            if entry.get("value") == {"applyLimitPerUniqueValue": True} and entry.get("limit") == 1
        }
        run_tags = mod.delta_table_run_tags("kpi_probe")
        self.assertEqual(run_tags, {mod.DELTA_CONCURRENCY_POOL_KEY: "kpi_probe"})
        self.assertIn(mod.DELTA_CONCURRENCY_POOL_KEY, configured_keys)
        with self.assertRaises(ValueError):
            mod.delta_table_run_tags("   ")

        probe_src = (REPO_ROOT / "lakehouse" / "delta" / "wp0_probes.py").read_text(encoding="utf-8")
        self.assertNotIn('op_tags={"dagster/concurrency_key"', probe_src)
        self.assertIn("tags=delta_table_run_tags(", probe_src)


if __name__ == "__main__":
    unittest.main()
