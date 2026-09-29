from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .model import Observation, SourceSnapshot
from .registry import geography_registry_json, indicator_registry_json
from .validation import coverage_ledger, validate_observations

CONTRACT_ID = "publicdata.indec-eph-labor-state/v1"
OBSERVATION_FIELDS = [
    "period", "geography_level", "geography_id", "geography_label",
    "indicator_id", "indicator_label", "value", "unit",
    "numerator_universe", "denominator_universe", "source_id",
    "source_publication_date", "source_snapshot_sha256", "source_cell_identity",
    "value_status", "quality_status", "cv", "ci90_low", "ci90_high",
    "exception_flags", "source_geography_code", "source_geography_label",
    "quality_source_id", "quality_source_snapshot_sha256", "quality_source_cell_identity",
]


def _obs_row(obs: Observation) -> dict[str, str]:
    row = asdict(obs)
    for field in ("value", "cv", "ci90_low", "ci90_high"):
        row[field] = "" if row[field] is None else str(row[field])
    row["exception_flags"] = json.dumps(row["exception_flags"], ensure_ascii=False, separators=(",", ":"))
    for k, v in list(row.items()):
        if v is None:
            row[k] = ""
    return row


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _release_id(observations: list[Observation], snapshots: list[SourceSnapshot]) -> str:
    payload = {
        "contract": CONTRACT_ID,
        "sources": sorted((s.source_id, s.sha256, s.layout_id) for s in snapshots),
        "cells": sorted((obs.key, str(obs.value), obs.value_status, obs.source_snapshot_sha256, obs.source_cell_identity) for obs in observations),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return f"indec-eph-labor-state-{digest}"


def write_release(output_root: Path, observations: list[Observation], snapshots: list[SourceSnapshot]) -> Path:
    validate_observations(observations)
    release_id = _release_id(observations, snapshots)
    release_dir = output_root / release_id
    if release_dir.exists():
        raise FileExistsError(f"immutable release already exists: {release_dir}")
    release_dir.mkdir(parents=True)

    data_path = release_dir / "labor_state.csv"
    with data_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OBSERVATION_FIELDS)
        writer.writeheader()
        for obs in sorted(observations, key=lambda x: x.key):
            writer.writerow(_obs_row(obs))

    coverage = coverage_ledger(observations)
    coverage_path = release_dir / "coverage.csv"
    with coverage_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["period", "geography_level", "geography_id", "indicator_id", "coverage_status"])
        writer.writeheader(); writer.writerows(coverage)

    (release_dir / "geographies.json").write_text(json.dumps(geography_registry_json(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (release_dir / "indicators.json").write_text(json.dumps(indicator_registry_json(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "contract_id": CONTRACT_ID,
        "release_id": release_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(observations),
        "period_min": min(obs.period for obs in observations),
        "period_max": max(obs.period for obs in observations),
        "required_coverage_window": ["2017-Q1", "2026-Q2"],
        "required_coverage_complete": all(r["coverage_status"] == "present" for r in coverage),
        "source_snapshots": [asdict(s) for s in snapshots],
        "files": {},
    }
    manifest_path = release_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    hashed_files = ["labor_state.csv", "coverage.csv", "geographies.json", "indicators.json"]
    manifest["files"] = {name: _sha256(release_dir / name) for name in hashed_files}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    checksums = {name: _sha256(release_dir / name) for name in [*hashed_files, "manifest.json"]}
    (release_dir / "checksums.sha256").write_text("".join(f"{sha}  {name}\n" for name, sha in sorted(checksums.items())), encoding="utf-8")
    return release_dir


def read_release_observations(release_dir: Path) -> list[dict[str, str]]:
    with (release_dir / "labor_state.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_release_files(release_dir: Path) -> None:
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        actual = _sha256(release_dir / name)
        if actual != expected:
            raise RuntimeError(f"release file checksum mismatch for {name}: declared={expected} actual={actual}")
