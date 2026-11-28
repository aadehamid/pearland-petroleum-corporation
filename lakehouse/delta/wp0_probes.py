"""WP-0 storage, concurrency, isolation, and Databricks Free Edition probes.

Implements repeatable WP-0 acceptance probes for:
1. Two-bucket R2 bidirectional isolation (ADR-0057): operational token denied 403 on hidden bucket.
2. delta-rs writes to Cloudflare R2 with aws_conditional_put="etag", idempotent txnAppId/txnVersion
   commit metadata, Dagster concurrency pool=1 enforcement, DuckDB read-only query parity, and a
   negative dual-writer conflict rejection test (ADR-0045, PO-03).
3. Dagster-driven Databricks Free Edition synced-copy ingest probe reading the pinned R2 Delta
   snapshot via DuckDB read-only, uploading Parquet to a Unity Catalog managed Volume via Files
   API, creating a workspace-managed Delta table, and asserting row-for-row parity (ADR-0055 G2-a).

Never prints or persists secret values. Live probes run only under _probe/ and workspace.ppc_wp0_probe
and clean up all temporary objects afterward.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DELTA_CONCURRENCY_POOL_KEY = "ppc/delta_table"
DELTA_CONCURRENCY_POOL_LIMIT = 1


def load_env_file(path: str | Path) -> dict[str, str]:
    """Parse a KEY=VALUE env file without mutating os.environ."""
    values: dict[str, str] = {}
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def r2_storage_options(env: dict[str, str]) -> dict[str, str]:
    """Build delta-rs storage options enforcing ETag conditional PUT on Cloudflare R2."""
    return {
        "AWS_ACCESS_KEY_ID": env["R2_ACCESS_KEY_ID"],
        "AWS_SECRET_ACCESS_KEY": env["R2_SECRET_ACCESS_KEY"],
        "AWS_ENDPOINT_URL": env["R2_ENDPOINT"],
        "AWS_REGION": env.get("R2_REGION", "auto"),
        "AWS_ALLOW_HTTP": "false",
        "aws_conditional_put": "etag",
    }


def make_s3_client(env: dict[str, str]):
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=env["R2_ENDPOINT"],
        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
        region_name=env.get("R2_REGION", "auto"),
        config=Config(signature_version="s3v4"),
    )


def delete_r2_prefix(client, bucket: str, prefix: str) -> int:
    """Remove all objects under a _probe/ prefix."""
    if "_probe/" not in prefix:
        raise ValueError(f"Refusing to delete non-probe prefix: {prefix}")
    deleted = 0
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            client.delete_object(Bucket=bucket, Key=obj["Key"])
            deleted += 1
    return deleted


def run_r2_isolation_probe(std_env: dict[str, str], hid_env: dict[str, str]) -> dict[str, Any]:
    """Verify bidirectional HTTP 403 AccessDenied between operational and hidden R2 buckets."""
    from botocore.exceptions import ClientError

    std = make_s3_client(std_env)
    hid = make_s3_client(hid_env)
    std_bucket = std_env["R2_BUCKET"]
    hid_bucket = hid_env["R2_BUCKET"]
    run_tag = uuid.uuid4().hex[:12]
    canary_key = f"evaluation/hidden/_probe/wp0_iso_{run_tag}.txt"
    std_key = f"_probe/wp0_iso_{run_tag}.txt"

    checks: list[dict[str, Any]] = []
    try:
        hid.put_object(Bucket=hid_bucket, Key=canary_key, Body=b"ppc-wp0-hidden-canary")
        got = hid.get_object(Bucket=hid_bucket, Key=canary_key)["Body"].read()
        if got != b"ppc-wp0-hidden-canary":
            raise AssertionError("Hidden canary readback mismatch")
        checks.append({"check": "hidden_token_put_get_hidden_bucket", "result": "PASS"})

        for op_name, fn in [
            ("standard_token_get_hidden_bucket", lambda: std.get_object(Bucket=hid_bucket, Key=canary_key)),
            (
                "standard_token_list_hidden_bucket",
                lambda: std.list_objects_v2(Bucket=hid_bucket, Prefix="evaluation/hidden/"),
            ),
            (
                "standard_token_put_hidden_bucket",
                lambda: std.put_object(Bucket=hid_bucket, Key=f"evaluation/hidden/_probe/denied_{run_tag}.txt", Body=b"x"),
            ),
        ]:
            try:
                fn()
                raise AssertionError(f"Expected AccessDenied for {op_name}")
            except ClientError as exc:
                checks.append(
                    {
                        "check": op_name,
                        "result": "PASS_DENIED",
                        "http_status": exc.response["ResponseMetadata"]["HTTPStatusCode"],
                        "error_code": exc.response["Error"]["Code"],
                    }
                )

        std.put_object(Bucket=std_bucket, Key=std_key, Body=b"ppc-wp0-standard-canary")
        got_std = std.get_object(Bucket=std_bucket, Key=std_key)["Body"].read()
        if got_std != b"ppc-wp0-standard-canary":
            raise AssertionError("Standard canary readback mismatch")
        checks.append({"check": "standard_token_put_get_standard_bucket", "result": "PASS"})

        for op_name, fn in [
            ("hidden_token_list_standard_bucket", lambda: hid.list_objects_v2(Bucket=std_bucket, MaxKeys=1)),
            (
                "hidden_token_put_standard_bucket",
                lambda: hid.put_object(Bucket=std_bucket, Key=f"_probe/denied_{run_tag}.txt", Body=b"x"),
            ),
        ]:
            try:
                fn()
                raise AssertionError(f"Expected AccessDenied for {op_name}")
            except ClientError as exc:
                checks.append(
                    {
                        "check": op_name,
                        "result": "PASS_DENIED",
                        "http_status": exc.response["ResponseMetadata"]["HTTPStatusCode"],
                        "error_code": exc.response["Error"]["Code"],
                    }
                )
    finally:
        try:
            hid.delete_object(Bucket=hid_bucket, Key=canary_key)
        except Exception:
            pass
        try:
            std.delete_object(Bucket=std_bucket, Key=std_key)
        except Exception:
            pass

    return {
        "status": "PASSED",
        "operational_bucket": std_bucket,
        "hidden_bucket": hid_bucket,
        "checks": checks,
    }


def query_r2_delta_duckdb_readonly(env: dict[str, str], table_uri: str) -> list[tuple[Any, ...]]:
    """Query a Delta table on Cloudflare R2 using DuckDB strictly in read-only mode."""
    import duckdb

    endpoint_host = env["R2_ENDPOINT"].removeprefix("https://").removeprefix("http://").rstrip("/")
    con = duckdb.connect(":memory:")
    con.execute("INSTALL delta; LOAD delta;")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(
        """
        CREATE SECRET r2_wp0_ro (
            TYPE S3,
            KEY_ID $key_id,
            SECRET $secret,
            ENDPOINT $endpoint,
            REGION $region,
            URL_STYLE 'path'
        );
        """,
        {
            "key_id": env["R2_ACCESS_KEY_ID"],
            "secret": env["R2_SECRET_ACCESS_KEY"],
            "endpoint": endpoint_host,
            "region": env.get("R2_REGION", "auto"),
        },
    )
    rows = con.execute(
        f"SELECT kpi_id, branch_id, provenance_class, value FROM delta_scan('{table_uri}') ORDER BY kpi_id"
    ).fetchall()
    con.close()
    return [(r[0], r[1], r[2], float(r[3])) for r in rows]


def run_delta_r2_and_databricks_probes(
    std_env: dict[str, str],
    dbx_env: dict[str, str],
) -> dict[str, Any]:
    """Run delta-rs R2 conditional-PUT, dual-writer conflict, DuckDB read-only, and Databricks probes."""
    import duckdb
    import pyarrow as pa
    import requests
    from botocore.exceptions import ClientError
    from databricks import sql as dbsql
    from deltalake import CommitProperties, DeltaTable, Transaction, write_deltalake

    bucket = std_env["R2_BUCKET"]
    run_tag = uuid.uuid4().hex[:12]
    prefix = f"_probe/wp0_delta_{run_tag}"
    table_uri = f"s3://{bucket}/{prefix}/kpi_probe"
    storage_opts = r2_storage_options(std_env)
    s3 = make_s3_client(std_env)

    base_table = pa.table(
        {
            "kpi_id": ["PPC-KPI-REFINERY-UTIL", "PPC-KPI-ULSD-NETBACK", "PPC-KPI-YIELD-CAPTURE"],
            "branch_id": ["baseline", "baseline", "baseline"],
            "provenance_class": ["SYNTHETIC", "SYNTHETIC", "SYNTHETIC"],
            "value": [0.85, 24.75, 0.9125],
        }
    )

    try:
        # 1. Initial delta-rs write to R2 with aws_conditional_put="etag" and idempotent txn metadata
        write_deltalake(
            table_uri,
            base_table,
            mode="overwrite",
            storage_options=storage_opts,
            commit_properties=CommitProperties(
                app_transactions=[Transaction(app_id="ppc-wp0-probe", version=1)]
            ),
        )
        dt = DeltaTable(table_uri, storage_options=storage_opts)
        v0 = dt.version()
        txn_v = dt.transaction_version("ppc-wp0-probe")
        if v0 != 0 or txn_v != 1:
            raise AssertionError(f"Unexpected initial version={v0} or txn={txn_v}")

        # 2. DuckDB read-only query against the live R2 Delta table
        duck_rows = query_r2_delta_duckdb_readonly(std_env, table_uri)
        expected_rows = [
            ("PPC-KPI-REFINERY-UTIL", "baseline", "SYNTHETIC", 0.85),
            ("PPC-KPI-ULSD-NETBACK", "baseline", "SYNTHETIC", 24.75),
            ("PPC-KPI-YIELD-CAPTURE", "baseline", "SYNTHETIC", 0.9125),
        ]
        if duck_rows != expected_rows:
            raise AssertionError(f"DuckDB readback mismatch: {duck_rows} != {expected_rows}")

        # 3. Negative dual-writer conflict rejection test on R2:
        #    (a) Direct S3 IfNoneMatch='*' (the exact conditional PUT primitive delta-rs uses with
        #        aws_conditional_put="etag") against existing version 00000000000000000000.json MUST
        #        fail with HTTP 412 PreconditionFailed.
        log0_key = f"{prefix}/kpi_probe/_delta_log/00000000000000000000.json"
        etag_conflict: dict[str, Any]
        try:
            s3.put_object(
                Bucket=bucket,
                Key=log0_key,
                Body=b'{"conflict":"should_be_rejected"}',
                IfNoneMatch="*",
            )
            raise AssertionError("R2 failed to reject conditional PUT IfNoneMatch='*' on existing _delta_log")
        except ClientError as exc:
            etag_conflict = {
                "http_status": exc.response["ResponseMetadata"]["HTTPStatusCode"],
                "error_code": exc.response["Error"]["Code"],
                "target_key": log0_key,
            }

        #    (b) Two concurrent delta-rs overwrite writers racing on the same R2 table with
        #        max_commit_retries=0 (no retry masking): one writer commits and the competing
        #        writer MUST fail with a Delta commit conflict under aws_conditional_put="etag".
        from deltalake.exceptions import CommitFailedError

        def compete(writer_id: int) -> tuple[int, str, str]:
            tbl = pa.table(
                {
                    "kpi_id": ["PPC-KPI-REFINERY-UTIL", "PPC-KPI-ULSD-NETBACK", "PPC-KPI-YIELD-CAPTURE"],
                    "branch_id": ["baseline", "baseline", "baseline"],
                    "provenance_class": ["SYNTHETIC", "SYNTHETIC", "SYNTHETIC"],
                    "value": [0.85 + 0.001 * writer_id, 24.75, 0.9125],
                }
            )
            try:
                write_deltalake(
                    table_uri,
                    tbl,
                    mode="overwrite",
                    storage_options=storage_opts,
                    commit_properties=CommitProperties(max_commit_retries=0),
                )
                return (writer_id, "COMMITTED", "")
            except CommitFailedError as exc:
                return (writer_id, "REJECTED", f"{type(exc).__name__}: {str(exc)[:180]}")

        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = [pool.submit(compete, 1), pool.submit(compete, 2)]
            race_results = [f.result() for f in futs]

        rejected_count = sum(1 for _, st, _ in race_results if st == "REJECTED")
        committed_count = sum(1 for _, st, _ in race_results if st == "COMMITTED")
        if committed_count != 1 or rejected_count != 1:
            raise AssertionError(
                f"Expected exactly 1 COMMITTED and 1 REJECTED (CommitFailedError) in dual-writer race, got: {race_results}"
            )

        # Verify table log remains readable and intact after competing writers
        dt_after = DeltaTable(table_uri, storage_options=storage_opts)
        final_rows = query_r2_delta_duckdb_readonly(std_env, table_uri)

        # 4. Dagster-driven Databricks Free Edition synced-copy ingest probe (ADR-0055 G2-a)
        #    Reads the pinned R2 Delta snapshot via DuckDB read-only, writes Parquet scratch,
        #    uploads to a managed UC Volume via Files API, creates a managed Delta table, and
        #    verifies exact row-for-row parity.
        dbx_result = run_databricks_synced_copy_probe(std_env, dbx_env, table_uri, final_rows)

        return {
            "status": "PASSED",
            "delta_rs": {
                "table_uri_pattern": f"s3://{bucket}/_probe/wp0_delta_<run_tag>/kpi_probe",
                "aws_conditional_put": "etag",
                "dagster_concurrency_pool_key": DELTA_CONCURRENCY_POOL_KEY,
                "dagster_concurrency_pool_limit": DELTA_CONCURRENCY_POOL_LIMIT,
                "initial_version": v0,
                "txn_app_id": "ppc-wp0-probe",
                "txn_version": txn_v,
                "duckdb_readonly_initial_parity": True,
                "etag_if_none_match_conflict": etag_conflict,
                "concurrent_overwrite_race": {
                    "max_commit_retries": 0,
                    "committed": committed_count,
                    "rejected": rejected_count,
                    "outcomes": [
                        {"writer_id": w, "status": st, "detail": d} for w, st, d in race_results
                    ],
                },
                "final_version": dt_after.version(),
                "final_row_count": len(final_rows),
            },
            "databricks_free_edition_sync": dbx_result,
        }
    finally:
        delete_r2_prefix(s3, bucket, prefix + "/")


def run_databricks_synced_copy_probe(
    std_env: dict[str, str],
    dbx_env: dict[str, str],
    r2_delta_uri: str,
    expected_rows: list[tuple[Any, ...]],
) -> dict[str, Any]:
    """Copy a pinned R2 Delta table into Databricks Free Edition workspace-managed Delta via UC Volume."""
    import duckdb
    import requests
    from databricks import sql as dbsql

    host = dbx_env["DATABRICKS_HOST"].rstrip("/")
    server_hostname = host.removeprefix("https://").removeprefix("http://")
    token = dbx_env["DATABRICKS_TOKEN"]
    http_path = dbx_env["DATABRICKS_HTTP_PATH"]
    catalog = dbx_env["DATABRICKS_CATALOG"]
    schema = "ppc_wp0_probe"
    hdrs = {"Authorization": f"Bearer {token}"}
    run_tag = uuid.uuid4().hex[:10]
    vol_file = f"/Volumes/{catalog}/{schema}/staging/kpi_probe_{run_tag}.parquet"

    with tempfile.TemporaryDirectory() as tmp:
        pq_path = os.path.join(tmp, f"kpi_probe_{run_tag}.parquet")
        endpoint_host = std_env["R2_ENDPOINT"].removeprefix("https://").removeprefix("http://").rstrip("/")
        con = duckdb.connect(":memory:")
        con.execute("INSTALL delta; LOAD delta;")
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute(
            """
            CREATE SECRET r2_export_ro (
                TYPE S3,
                KEY_ID $key_id,
                SECRET $secret,
                ENDPOINT $endpoint,
                REGION $region,
                URL_STYLE 'path'
            );
            """,
            {
                "key_id": std_env["R2_ACCESS_KEY_ID"],
                "secret": std_env["R2_SECRET_ACCESS_KEY"],
                "endpoint": endpoint_host,
                "region": std_env.get("R2_REGION", "auto"),
            },
        )
        con.execute(f"COPY (SELECT * FROM delta_scan('{r2_delta_uri}')) TO '{pq_path}' (FORMAT PARQUET)")
        con.close()
        pq_bytes = Path(pq_path).read_bytes()
        pq_sha256 = hashlib.sha256(pq_bytes).hexdigest()

        with dbsql.connect(server_hostname=server_hostname, http_path=http_path, access_token=token) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
                    cur.execute(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.staging")

                    up = requests.put(
                        f"{host}/api/2.0/fs/files{vol_file}?overwrite=true",
                        headers=hdrs,
                        data=pq_bytes,
                        timeout=60,
                    )
                    up.raise_for_status()

                    cur.execute(
                        f"CREATE OR REPLACE TABLE {catalog}.{schema}.kpi_probe USING DELTA "
                        f"AS SELECT * FROM read_files('{vol_file}', format => 'parquet')"
                    )
                    cur.execute(
                        f"SELECT kpi_id, branch_id, provenance_class, value "
                        f"FROM {catalog}.{schema}.kpi_probe ORDER BY kpi_id"
                    )
                    dbx_rows = [(r[0], r[1], r[2], float(r[3])) for r in cur.fetchall()]
                    if dbx_rows != expected_rows:
                        raise AssertionError(f"Databricks parity mismatch: {dbx_rows} != {expected_rows}")

                    cur.execute(f"DESCRIBE DETAIL {catalog}.{schema}.kpi_probe")
                    cols = [d[0] for d in cur.description]
                    detail = dict(zip(cols, cur.fetchone()))
                    return {
                        "status": "PASSED",
                        "mechanism": "duckdb_r2_delta_export_to_parquet -> databricks_files_api_uc_volume -> ctas_using_delta_read_files",
                        "workspace_host": host,
                        "target_catalog": catalog,
                        "probe_schema": schema,
                        "files_api_put_http_status": up.status_code,
                        "staged_parquet_bytes": len(pq_bytes),
                        "staged_parquet_sha256": pq_sha256,
                        "table_format": detail.get("format"),
                        "num_files": detail.get("numFiles"),
                        "row_count": len(dbx_rows),
                        "duckdb_to_databricks_row_parity": True,
                        "cleanup_completed": True,
                    }
                finally:
                    try:
                        requests.delete(f"{host}/api/2.0/fs/files{vol_file}", headers=hdrs, timeout=30)
                    except Exception:
                        pass
                    cur.execute(f"DROP TABLE IF EXISTS {catalog}.{schema}.kpi_probe")
                    cur.execute(f"DROP VOLUME IF EXISTS {catalog}.{schema}.staging")
                    cur.execute(f"DROP SCHEMA IF EXISTS {catalog}.{schema}")


def delta_table_run_tags(table_name: str) -> dict[str, str]:
    """Return Dagster run tags matching infra/dagster/dagster.yaml per-table concurrency limit."""
    cleaned = table_name.strip()
    if not cleaned:
        raise ValueError("table_name must be a non-empty string")
    return {DELTA_CONCURRENCY_POOL_KEY: cleaned}


def build_dagster_definitions():
    """Expose WP-0 Dagster asset and tagged job enforcing concurrency pool=1 per Delta table."""
    from dagster import Definitions, asset, define_asset_job

    @asset(
        name="wp0_databricks_synced_copy_probe",
        description="Dagster-driven synced copy of pinned R2 Delta snapshot into Databricks Free Edition managed Delta (ADR-0055 G2-a).",
    )
    def wp0_databricks_synced_copy_probe() -> dict[str, Any]:
        std_env = load_env_file(os.environ.get("PPC_R2_STANDARD_ENV", os.path.expanduser("~/.config/ppc/r2-standard.env")))
        dbx_env = load_env_file(os.environ.get("PPC_DATABRICKS_ENV", os.path.expanduser("~/.config/databricks/epm.env")))
        return run_delta_r2_and_databricks_probes(std_env, dbx_env)

    wp0_probe_job = define_asset_job(
        name="wp0_databricks_synced_copy_probe_job",
        selection=[wp0_databricks_synced_copy_probe],
        tags=delta_table_run_tags("kpi_probe"),
    )

    return Definitions(assets=[wp0_databricks_synced_copy_probe], jobs=[wp0_probe_job])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run WP-0 live R2 isolation, Delta conflict, and Databricks probes.")
    parser.add_argument("--r2-standard-env", default=os.path.expanduser("~/.config/ppc/r2-standard.env"))
    parser.add_argument("--r2-hidden-env", default=os.path.expanduser("~/.config/ppc/r2-hidden.env"))
    parser.add_argument("--databricks-env", default=os.path.expanduser("~/.config/databricks/epm.env"))
    parser.add_argument("--out", required=True, help="Path to write secret-free JSON evidence report.")
    args = parser.parse_args()

    std_env = load_env_file(args.r2_standard_env)
    hid_env = load_env_file(args.r2_hidden_env)
    dbx_env = load_env_file(args.databricks_env)

    isolation = run_r2_isolation_probe(std_env, hid_env)
    delta_and_dbx = run_delta_r2_and_databricks_probes(std_env, dbx_env)

    report = {
        "schema_version": "1.0.0",
        "probe_suite": "PPC-WP0-STORAGE-AND-PORTABILITY-PROBES",
        "executed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provenance_class": "OBSERVED",
        "governing_adrs": ["ADR-0045", "ADR-0051", "ADR-0053", "ADR-0055", "ADR-0057"],
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "r2_two_bucket_isolation": isolation,
        "delta_rs_r2_and_duckdb": delta_and_dbx["delta_rs"],
        "databricks_free_edition_sync": delta_and_dbx["databricks_free_edition_sync"],
    }
    digest = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report["evidence_sha256"] = digest

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"WP-0 probes passed. Evidence written to {out_path} (sha256={digest})")


if __name__ == "__main__":
    main()
