#!/usr/bin/env python3
"""WP-1a public data ingestion landing pinned OBSERVED vintages to Cloudflare R2 raw/.

Ingests verified primary public observations (EIA Open Data API v2 PADD 3 stocks
and inputs, USGC refined-product spot prices, WTI Cushing, Europe Brent, and
Henry Hub natural gas; NOAA NHC HURDAT2 Atlantic best-track archive; and EPA
Envirofacts GHGRP facility registry PUB_DIM_FACILITY NAICS 324110 TX/LA subset
of PADD 3) into the operational R2 bucket under
`raw/external/{eia,noaa,epa,phmsa}/vintage=<date>/` and writes a secret-free
`OBSERVED` vintage manifest. PHMSA hazardous liquid incident ZIP archives are
ingested only when explicitly supplied via `--phmsa-zip`; otherwise the manifest
records `DEFERRED_MANUAL_ARCHIVE`.

Governing authorities: PPC-WORLD-001 §4, PPC-PLAN-001 WP-1, PPC-013, ADR-0051, ADR-0057.
Never commits or prints API keys or R2 credentials.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import time
import urllib.parse
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


GENERATOR_VERSION = "wp1-public-ingest-1.0.0"
EIA_BASE_URL = "https://api.eia.gov/v2"
NOAA_HURDAT2_URL = "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-092326.txt"
EPA_GHGRP_BASE_URL = "https://data.epa.gov/efservice"
PHMSA_ARCHIVE_URL = (
    "https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/data_statistics/pipeline/"
    "accident_hazardous_liquid_jan2010_present.zip"
)

# Live-verified EIA Open Data API v2 benchmark catalog (queried by facets[series][])
EIA_SERIES_CATALOG: tuple[dict[str, str], ...] = (
    {
        "series_id": "WCRRIP32",
        "route": "petroleum/pnp/wiup/data/",
        "frequency": "weekly",
        "unit": "MBBL/D",
        "description": "PADD 3 refiner net inputs of crude oil",
    },
    {
        "series_id": "WGIRIP32",
        "route": "petroleum/pnp/wiup/data/",
        "frequency": "weekly",
        "unit": "MBBL/D",
        "description": "PADD 3 refiner gross inputs to atmospheric crude oil distillation units",
    },
    {
        "series_id": "WCESTP31",
        "route": "petroleum/stoc/wstk/data/",
        "frequency": "weekly",
        "unit": "MBBL",
        "description": "PADD 3 ending stocks excluding SPR of crude oil",
    },
    {
        "series_id": "WD0ST_R30_1",
        "route": "petroleum/stoc/wstk/data/",
        "frequency": "weekly",
        "unit": "MBBL",
        "description": "PADD 3 ending stocks of ultra-low sulfur (0-15 ppm) distillate",
    },
    {
        "series_id": "WGTSTP31",
        "route": "petroleum/stoc/wstk/data/",
        "frequency": "weekly",
        "unit": "MBBL",
        "description": "PADD 3 ending stocks of total motor gasoline",
    },
    {
        "series_id": "WO6ST_R30_1",
        "route": "petroleum/stoc/wstk/data/",
        "frequency": "weekly",
        "unit": "MBBL",
        "description": "PADD 3 ending stocks of CBOB gasoline blending components",
    },
    {
        "series_id": "W_EPOBGRR_SAE_R30_MBBL",
        "route": "petroleum/stoc/wstk/data/",
        "frequency": "weekly",
        "unit": "MBBL",
        "description": "PADD 3 ending stocks of RBOB gasoline blending components",
    },
    {
        "series_id": "RWTC",
        "route": "petroleum/pri/spt/data/",
        "frequency": "daily",
        "unit": "$/BBL",
        "description": "Cushing, OK WTI spot price FOB",
    },
    {
        "series_id": "RBRTE",
        "route": "petroleum/pri/spt/data/",
        "frequency": "daily",
        "unit": "$/BBL",
        "description": "Europe Brent spot price FOB",
    },
    {
        "series_id": "EER_EPD2DXL0_PF4_RGC_DPG",
        "route": "petroleum/pri/spt/data/",
        "frequency": "daily",
        "unit": "$/GAL",
        "description": "U.S. Gulf Coast ultra-low sulfur No 2 diesel spot price",
    },
    {
        "series_id": "EER_EPMRU_PF4_RGC_DPG",
        "route": "petroleum/pri/spt/data/",
        "frequency": "daily",
        "unit": "$/GAL",
        "description": "U.S. Gulf Coast conventional gasoline regular spot price",
    },
    {
        "series_id": "EER_EPJK_PF4_RGC_DPG",
        "route": "petroleum/pri/spt/data/",
        "frequency": "daily",
        "unit": "$/GAL",
        "description": "U.S. Gulf Coast kerosene-type jet fuel spot price",
    },
    {
        "series_id": "EER_EPLLPA_PF4_Y44MB_DPG",
        "route": "petroleum/pri/spt/data/",
        "frequency": "daily",
        "unit": "$/GAL",
        "description": "Mont Belvieu, TX propane spot price FOB",
    },
    {
        "series_id": "RNGWHHD",
        "route": "natural-gas/pri/fut/data/",
        "frequency": "daily",
        "unit": "$/MMBTU",
        "description": "Henry Hub natural gas spot price",
    },
)


@dataclass(frozen=True)
class IngestedObject:
    source: str
    name: str
    r2_key: str
    sha256: str
    size_bytes: int
    row_count: int
    unit: str | None
    date_min: str | None
    date_max: str | None
    uploaded: bool
    r2_etag: str | None = None
    provenance_class: str = "OBSERVED"


def load_env_file(path: str | Path) -> dict[str, str]:
    """Load simple KEY=VALUE lines from an env file outside Git without printing values."""
    env: dict[str, str] = {}
    for raw_line in Path(path).expanduser().read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_eia_query_url(
    route: str,
    series_id: str,
    frequency: str,
    start_date: str,
    end_date: str,
    api_key: str,
    offset: int = 0,
    length: int = 5000,
) -> str:
    """Build a paginated EIA Open Data API v2 request URL (never log the returned URL)."""
    if length <= 0 or length > 5000:
        raise ValueError("EIA API v2 length must be between 1 and 5000")
    params = [
        ("api_key", api_key),
        ("frequency", frequency),
        ("data[0]", "value"),
        ("facets[series][]", series_id),
        ("start", start_date),
        ("end", end_date),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "asc"),
        ("offset", str(offset)),
        ("length", str(length)),
    ]
    return f"{EIA_BASE_URL}/{route.lstrip('/')}?{urllib.parse.urlencode(params)}"


def fetch_eia_series(
    entry: dict[str, str],
    api_key: str,
    start_date: str,
    end_date: str,
    http_get: Callable[[str], bytes],
    sleep_seconds: float = 0.25,
) -> list[dict[str, Any]]:
    """Fetch all paginated rows for one EIA API v2 series."""
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        url = build_eia_query_url(
            route=entry["route"],
            series_id=entry["series_id"],
            frequency=entry["frequency"],
            start_date=start_date,
            end_date=end_date,
            api_key=api_key,
            offset=offset,
            length=5000,
        )
        raw = http_get(url)
        payload = json.loads(raw.decode("utf-8"))
        resp = payload.get("response", {})
        batch = resp.get("data", [])
        if not isinstance(batch, list):
            raise ValueError(f"Unexpected EIA payload structure for {entry['series_id']}")
        if "total" not in resp:
            raise ValueError(f"EIA response missing required 'total' field for {entry['series_id']}")
        total = int(resp["total"])
        if total <= 0:
            raise ValueError(
                f"EIA series {entry['series_id']} reported non-positive total={total} for window {start_date}..{end_date}"
            )
        for row in batch:
            row_series = row.get("series")
            if row_series is None or str(row_series) != entry["series_id"]:
                raise ValueError(
                    f"EIA series filter mismatch: requested {entry['series_id']}, got {row_series!r}"
                )
            row_period = str(row.get("period", "")).strip()
            if not row_period or not (start_date <= row_period <= end_date):
                raise ValueError(
                    f"EIA period {row_period!r} outside pinned window [{start_date}, {end_date}] for {entry['series_id']}"
                )
        rows.extend(batch)
        offset += len(batch)
        if offset >= total:
            break
        if not batch:
            raise ValueError(
                f"EIA series {entry['series_id']} truncated at {offset} of {total} rows (empty page before total)"
            )
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    if not rows or len(rows) != total:
        raise ValueError(
            f"EIA series {entry['series_id']} returned {len(rows)} rows, expected total={total}"
        )
    periods_seen = [str(r.get("period", "")) for r in rows]
    if len(set(periods_seen)) != len(periods_seen):
        raise ValueError(
            f"EIA series {entry['series_id']} contains duplicate periods ({len(periods_seen)} rows, {len(set(periods_seen))} unique)"
        )
    return rows


def fetch_epa_ghgrp_state(
    state: str,
    http_get: Callable[[str], bytes],
    page_size: int = 500,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Fetch all paginated EPA Envirofacts GHGRP NAICS 324110 records for one state."""
    records: list[dict[str, Any]] = []
    seen_row_keys: set[tuple[str, str]] = set()
    start = 0
    for _ in range(max_pages):
        end = start + page_size - 1  # Envirofacts ROWS/start:end is inclusive
        epa_url = f"{EPA_GHGRP_BASE_URL}/PUB_DIM_FACILITY/NAICS_CODE/324110/STATE/{state}/ROWS/{start}:{end}/JSON"
        epa_raw = http_get(epa_url)
        parsed = json.loads(epa_raw.decode("utf-8"))
        if not isinstance(parsed, list):
            raise ValueError(f"Unexpected EPA Envirofacts response structure for state {state}")
        for rec in parsed:
            rec_state = rec.get("state") if rec.get("state") is not None else rec.get("STATE")
            if rec_state is None or str(rec_state).strip().upper() != state.upper():
                raise ValueError(f"EPA state filter mismatch: requested {state}, got {rec_state!r}")
            rec_naics = rec.get("naics_code") if rec.get("naics_code") is not None else rec.get("NAICS_CODE")
            if rec_naics is None or str(rec_naics).strip() != "324110":
                raise ValueError(f"EPA NAICS filter mismatch: requested 324110, got {rec_naics!r}")
            rec_fac = rec.get("facility_id") if rec.get("facility_id") is not None else rec.get("FACILITY_ID")
            if rec_fac is None or not str(rec_fac).strip():
                raise ValueError(f"EPA record missing non-blank facility_id / FACILITY_ID for state {state}")
            rec_year = rec.get("year") if rec.get("year") is not None else rec.get("YEAR")
            if rec_year is not None:
                rkey = (str(rec_fac).strip(), str(rec_year).strip())
                if rkey in seen_row_keys:
                    raise ValueError(f"Duplicate EPA (facility_id, year) row detected across pages: {rkey}")
                seen_row_keys.add(rkey)
        records.extend(parsed)
        if len(parsed) < page_size:
            return records
        start += len(parsed)
    raise RuntimeError(f"EPA Envirofacts pagination exceeded {max_pages} pages for state {state}")


def parse_hurdat2_storms(raw_text: str, min_year: int = 2010) -> list[dict[str, Any]]:
    """Parse NOAA NHC HURDAT2 best-track ASCII format into structured storm summaries."""
    storms: list[dict[str, Any]] = []
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    i = 0
    while i < len(lines):
        header_parts = [p.strip() for p in lines[i].split(",")]
        if len(header_parts) < 3 or not header_parts[0][:2].isalpha():
            raise ValueError(f"Unreadable HURDAT2 header at line {i + 1}: {lines[i]!r}")
        storm_id = header_parts[0]
        storm_name = header_parts[1]
        n_rows = int(header_parts[2])
        track_lines = lines[i + 1 : i + 1 + n_rows]
        if len(track_lines) != n_rows:
            raise ValueError(f"Truncated HURDAT2 track for {storm_id}: expected {n_rows}, got {len(track_lines)}")
        year = int(storm_id[4:8])
        max_wind_kt = 0
        min_pres_mb: int | None = None
        statuses: set[str] = set()
        for tline in track_lines:
            cols = [c.strip() for c in tline.split(",")]
            if len(cols) < 8:
                raise ValueError(f"Malformed HURDAT2 track row for {storm_id} (<8 columns): {tline!r}")
            statuses.add(cols[3])
            wind = int(cols[6])
            if wind > max_wind_kt:
                max_wind_kt = wind
            pres = int(cols[7])
            if pres > 0 and (min_pres_mb is None or pres < min_pres_mb):
                min_pres_mb = pres
        if year >= min_year:
            storms.append(
                {
                    "storm_id": storm_id,
                    "name": storm_name,
                    "year": year,
                    "track_points": n_rows,
                    "max_wind_kt": max_wind_kt,
                    "min_pressure_mb": min_pres_mb,
                    "reached_hurricane": "HU" in statuses,
                }
            )
        i += 1 + n_rows
    return storms


def parse_phmsa_liquid_zip(zip_bytes: bytes) -> list[dict[str, Any]]:
    """Parse a PHMSA Form 7000-1 hazardous liquid incident ZIP archive into normalized rows."""
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_names = sorted(n for n in zf.namelist() if n.lower().endswith((".csv", ".txt")))
        if not csv_names:
            raise ValueError("PHMSA ZIP archive contains no CSV/TXT data file")
        matched_members: list[str] = []
        seen_reports: set[str] = set()
        for member in csv_names:
            with zf.open(member) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8-sig", errors="replace")
                first_line = text.readline()
                if not first_line:
                    continue
                delimiter = "\t" if "\t" in first_line else ","
                headers = {h.strip().strip('"') for h in first_line.split(delimiter)}
                if "REPORT_NUMBER" not in headers:
                    continue
                matched_members.append(member)
                text.seek(0)
                reader = csv.DictReader(text, delimiter=delimiter)
                for row_num, row in enumerate(reader, start=2):
                    if not any((v or "").strip() for v in row.values()):
                        continue
                    rep_no = (row.get("REPORT_NUMBER") or "").strip()
                    if not rep_no:
                        raise ValueError(f"PHMSA archive member {member} row {row_num} missing REPORT_NUMBER")
                    if rep_no in seen_reports:
                        raise ValueError(f"PHMSA archive contains duplicate REPORT_NUMBER {rep_no!r} (member {member})")
                    seen_reports.add(rep_no)
                    rows.append(
                        {
                            "report_number": rep_no,
                            "year": row.get("I_YEAR", "").strip(),
                            "state": row.get("ACCIDENT_STATE_ABBREVIATION", "").strip(),
                            "commodity": row.get("COMMODITY_RELEASED_TYPE", "").strip(),
                            "cause": row.get("CAUSE", "").strip(),
                            "provenance_class": "OBSERVED",
                        }
                    )
        if not matched_members:
            raise ValueError("PHMSA ZIP archive contains no CSV/TXT member with REPORT_NUMBER header")
    if not rows:
        raise ValueError("PHMSA ZIP archive parsed 0 valid incident rows")
    return rows


def make_r2_client(r2_env: dict[str, str]):
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=r2_env["R2_ENDPOINT"],
        aws_access_key_id=r2_env["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=r2_env["R2_SECRET_ACCESS_KEY"],
        region_name=r2_env.get("R2_REGION", "auto"),
        config=Config(signature_version="s3v4"),
    )


def sanitize_url_for_logs(url: str) -> str:
    """Redact api_key query parameters so secrets never appear in errors or logs."""
    return re.sub(r"(api_key=)[^&]+", r"\1REDACTED", url)


def default_http_get(url: str) -> bytes:
    import requests

    try:
        resp = requests.get(url, timeout=60, headers={"User-Agent": "PPC-PublicDataIngest/1.0"})
        if resp.status_code == 429:
            time.sleep(2.0)
            resp = requests.get(url, timeout=60, headers={"User-Agent": "PPC-PublicDataIngest/1.0"})
        if resp.status_code >= 400:
            raise RuntimeError(
                f"HTTP {resp.status_code} error fetching {sanitize_url_for_logs(url)}"
            )
        return resp.content
    except requests.RequestException as exc:
        raise RuntimeError(
            f"HTTP transport error ({type(exc).__name__}) fetching {sanitize_url_for_logs(url)}"
        ) from None


def run_public_ingest(
    vintage: str,
    start_date: str,
    end_date: str,
    eia_api_key: str,
    http_get: Callable[[str], bytes],
    upload_fn: Callable[[str, bytes, str], str | None] | None = None,
    phmsa_zip_bytes: bytes | None = None,
    target_bucket: str = "pearland-petroleum-corp",
) -> dict[str, Any]:
    """Run public ingestion producing deterministic raw data objects and a timestamped OBSERVED manifest."""
    if "hidden" in target_bucket.lower():
        raise ValueError("Public raw ingestion must never target the hidden-truth bucket (ADR-0057)")
    ingested: list[IngestedObject] = []

    def emit(
        source: str,
        name: str,
        rel_key: str,
        payload: bytes,
        content_type: str,
        row_count: int,
        unit: str | None = None,
        date_min: str | None = None,
        date_max: str | None = None,
    ):
        r2_key = f"raw/external/{source}/vintage={vintage}/{rel_key}"
        uploaded = upload_fn is not None
        etag: str | None = None
        expected_md5 = hashlib.md5(payload).hexdigest()
        if upload_fn is not None:
            raw_etag = upload_fn(r2_key, payload, content_type)
            etag = str(raw_etag).strip('"') if raw_etag else None
            if not etag or etag != expected_md5:
                raise RuntimeError(
                    f"R2 upload ETag verification failed for {r2_key}: expected md5={expected_md5}, got {etag!r}"
                )
        ingested.append(
            IngestedObject(
                source=source,
                name=name,
                r2_key=r2_key,
                sha256=sha256_bytes(payload),
                size_bytes=len(payload),
                row_count=row_count,
                unit=unit,
                date_min=date_min,
                date_max=date_max,
                uploaded=uploaded,
                r2_etag=etag,
            )
        )

    # 1. EIA Open Data API v2 series (PADD 3 + USGC + Henry Hub)
    eia_summary: dict[str, Any] = {}
    for entry in EIA_SERIES_CATALOG:
        rows = fetch_eia_series(entry, eia_api_key, start_date, end_date, http_get=http_get)
        periods = sorted(str(r["period"]) for r in rows if r.get("period"))
        doc = {
            "provenance_class": "OBSERVED",
            "source": "EIA_API_V2",
            "series_id": entry["series_id"],
            "route": entry["route"],
            "frequency": entry["frequency"],
            "unit": entry["unit"],
            "description": entry["description"],
            "vintage": vintage,
            "row_count": len(rows),
            "data": rows,
        }
        raw_bytes = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
        emit(
            source="eia",
            name=entry["series_id"],
            rel_key=f"{entry['series_id']}.json",
            payload=raw_bytes,
            content_type="application/json",
            row_count=len(rows),
            unit=entry["unit"],
            date_min=periods[0] if periods else None,
            date_max=periods[-1] if periods else None,
        )
        numeric_pairs = sorted(
            (
                (str(r.get("period", "")), float(r["value"]))
                for r in rows
                if r.get("value") not in (None, "")
            ),
            key=lambda pair: pair[0],
        )
        numeric_vals = [v for _, v in numeric_pairs]
        eia_summary[entry["series_id"]] = {
            "unit": entry["unit"],
            "frequency": entry["frequency"],
            "row_count": len(rows),
            "date_min": periods[0] if periods else None,
            "date_max": periods[-1] if periods else None,
            "latest_value": numeric_pairs[-1][1] if numeric_pairs else None,
            "latest_value_period": numeric_pairs[-1][0] if numeric_pairs else None,
            "min_value": min(numeric_vals) if numeric_vals else None,
            "max_value": max(numeric_vals) if numeric_vals else None,
        }

    # 2. NOAA NHC HURDAT2 Atlantic best-track archive (full 1851-present payload)
    hurdat_raw = http_get(NOAA_HURDAT2_URL)
    all_storms = parse_hurdat2_storms(hurdat_raw.decode("utf-8", errors="replace"), min_year=0)
    if not all_storms:
        raise ValueError("NOAA HURDAT2 archive parsed 0 storm records")
    storms_since_2010 = [s for s in all_storms if s["year"] >= 2010]
    emit(
        source="noaa",
        name="hurdat2_atlantic_best_track",
        rel_key="hurdat2_atlantic.txt",
        payload=hurdat_raw,
        content_type="text/plain",
        row_count=len(all_storms),
        unit="storm_records",
        date_min=str(min(s["year"] for s in all_storms)),
        date_max=str(max(s["year"] for s in all_storms)),
    )

    # 3. EPA Envirofacts GHGRP facility registry (PUB_DIM_FACILITY, NAICS 324110, TX & LA subset of PADD 3)
    epa_records: list[dict[str, Any]] = []
    for state in ("TX", "LA"):
        epa_records.extend(fetch_epa_ghgrp_state(state, http_get=http_get))
    if not epa_records:
        raise ValueError("EPA Envirofacts GHGRP query returned 0 records for TX/LA NAICS 324110")
    epa_payload = json.dumps(
        {"provenance_class": "OBSERVED", "source": "EPA_ENVIROFACTS_GHGRP", "naics": "324110", "records": epa_records},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    unique_facilities = {
        str(r.get("facility_id") if r.get("facility_id") is not None else r.get("FACILITY_ID")).strip()
        for r in epa_records
        if (r.get("facility_id") is not None or r.get("FACILITY_ID") is not None)
    }
    if not unique_facilities:
        raise ValueError("EPA Envirofacts GHGRP records contained no facility_id / FACILITY_ID keys")
    emit(
        source="epa",
        name="ghgrp_naics_324110_tx_la",
        rel_key="ghgrp_naics_324110_tx_la.json",
        payload=epa_payload,
        content_type="application/json",
        row_count=len(epa_records),
        unit="facility_year_rows",
    )

    # 4. PHMSA hazardous liquid archive (ingested only when --phmsa-zip is explicitly supplied; never bypasses anti-bot gates)
    phmsa_status = "DEFERRED_MANUAL_ARCHIVE"
    if phmsa_zip_bytes is not None:
        phmsa_rows = parse_phmsa_liquid_zip(phmsa_zip_bytes)
        emit(
            source="phmsa",
            name="hazardous_liquid_accidents_2010_present",
            rel_key="accident_hazardous_liquid.zip",
            payload=phmsa_zip_bytes,
            content_type="application/zip",
            row_count=len(phmsa_rows),
            unit="incident_rows",
        )
        phmsa_status = "INGESTED" if upload_fn is not None else "PARSED_LOCAL_DRY_RUN"

    manifest: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generator_version": GENERATOR_VERSION,
        "code_file": "generators/public_ingest.py",
        "manifest_kind": "PPC-WP1-PUBLIC-DATA-VINTAGE",
        "provenance_class": "OBSERVED",
        "upload_status": "UPLOADED_TO_R2" if upload_fn is not None else "LOCAL_DRY_RUN_NOT_UPLOADED",
        "vintage": vintage,
        "window": {"start_date": start_date, "end_date": end_date},
        "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "governing_adrs": ["ADR-0051", "ADR-0057"],
        "r2_bucket": target_bucket if upload_fn is not None else None,
        "target_r2_bucket": target_bucket,
        "sources": {
            "eia": {"series_count": len(EIA_SERIES_CATALOG), "series": eia_summary},
            "noaa": {
                "archive_url": NOAA_HURDAT2_URL,
                "total_storms_in_archive": len(all_storms),
                "archive_year_min": min(s["year"] for s in all_storms),
                "archive_year_max": max(s["year"] for s in all_storms),
                "storms_since_2010": len(storms_since_2010),
                "hurricanes_since_2010": sum(1 for s in storms_since_2010 if s["reached_hurricane"]),
            },
            "epa": {
                "table": "PUB_DIM_FACILITY",
                "naics": "324110",
                "states": ["TX", "LA"],
                "row_count": len(epa_records),
                "unique_facilities": len(unique_facilities),
                "rfs_rin_status": "DEFERRED_RFS_RIN_CONTEXT",
            },
            "phmsa": {"status": phmsa_status, "archive_url": PHMSA_ARCHIVE_URL},
        },
        "objects": [
            {
                "source": o.source,
                "name": o.name,
                "r2_key": o.r2_key,
                "sha256": o.sha256,
                "size_bytes": o.size_bytes,
                "row_count": o.row_count,
                "unit": o.unit,
                "date_min": o.date_min,
                "date_max": o.date_max,
                "uploaded": o.uploaded,
                "r2_etag": o.r2_etag,
                "provenance_class": o.provenance_class,
            }
            for o in ingested
        ],
    }
    digest = sha256_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    manifest["manifest_sha256"] = digest
    if upload_fn is not None:
        manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
        expected_manifest_md5 = hashlib.md5(manifest_bytes).hexdigest()
        manifest_key = f"manifests/ingestion/public_vintage_{vintage}.json"
        raw_etag = upload_fn(manifest_key, manifest_bytes, "application/json")
        etag = str(raw_etag).strip('"') if raw_etag else None
        if not etag or etag != expected_manifest_md5:
            raise RuntimeError(
                f"R2 upload ETag verification failed for {manifest_key}: expected md5={expected_manifest_md5}, got {etag!r}"
            )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest pinned OBSERVED public feeds to Cloudflare R2 raw/.")
    parser.add_argument("--vintage", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--start-date", default="2024-01-01")
    parser.add_argument("--end-date", default="2025-12-31")
    parser.add_argument("--eia-env", default=os.path.expanduser("~/.config/eia/api.env"))
    parser.add_argument("--r2-env", default=os.path.expanduser("~/.config/ppc/r2-standard.env"))
    parser.add_argument("--phmsa-zip", default=None, help="Optional local PHMSA Form 7000-1 ZIP archive path.")
    parser.add_argument("--out", required=True, help="Path to write secret-free OBSERVED vintage manifest JSON.")
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip R2 upload; still fetches public feeds over the network and writes the manifest locally.",
    )
    args = parser.parse_args()

    eia_env = load_env_file(args.eia_env)
    api_key = eia_env.get("EIA_API_KEY")
    if not api_key:
        raise KeyError(f"EIA_API_KEY missing from {args.eia_env}")

    upload_fn = None
    r2_env_path = Path(args.r2_env).expanduser()
    if args.no_upload:
        target_bucket = load_env_file(r2_env_path).get("R2_BUCKET", "UNCONFIGURED_LOCAL_DRY_RUN") if r2_env_path.exists() else "UNCONFIGURED_LOCAL_DRY_RUN"
    else:
        r2_env = load_env_file(r2_env_path)
        target_bucket = r2_env["R2_BUCKET"]
        if "hidden" in target_bucket.lower():
            raise ValueError("Public raw ingestion must never write to the hidden-truth bucket (ADR-0057)")
        s3 = make_r2_client(r2_env)

        def _put(key: str, data: bytes, ctype: str) -> str | None:
            resp = s3.put_object(Bucket=target_bucket, Key=key, Body=data, ContentType=ctype)
            return str(resp.get("ETag", "")).strip('"') or None

        upload_fn = _put

    phmsa_bytes = Path(args.phmsa_zip).read_bytes() if args.phmsa_zip else None
    manifest = run_public_ingest(
        vintage=args.vintage,
        start_date=args.start_date,
        end_date=args.end_date,
        eia_api_key=api_key,
        http_get=default_http_get,
        upload_fn=upload_fn,
        phmsa_zip_bytes=phmsa_bytes,
        target_bucket=target_bucket,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"WP-1a public ingest complete: {len(manifest['objects'])} objects (sha256={manifest['manifest_sha256']})")


if __name__ == "__main__":
    main()
