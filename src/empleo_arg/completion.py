"""Bounded model-use completion overlays for documented official gaps."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from .periods import iter_quarters
from .registry import CORE_INDICATORS, REQUIRED_GEOGRAPHIES, GEO_BY_ID
from .release import read_release_observations, verify_release_files

CONTRACT_ID = "research.indec-eph-labor-context-completion/v1"
FIELDS = [
    "period", "geography_level", "geography_id", "indicator_id", "value",
    "value_status", "fill_method", "fill_source_period", "fill_distance_quarters",
    "official_parent_release_id", "official_parent_manifest_sha256",
    "source_observation_identity",
]


class CompletionError(ValueError):
    pass


def _quarter_offset(period: str, delta: int) -> str:
    year, quarter = int(period[:4]), int(period[-1])
    index = year * 4 + quarter - 1 + delta
    return f"{index // 4:04d}-Q{index % 4 + 1}"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _required_keys() -> list[tuple[str, str, str, str]]:
    return [
        (period, GEO_BY_ID[geo].geography_level, geo, indicator)
        for period in iter_quarters("2017-Q1", "2026-Q2")
        for geo in REQUIRED_GEOGRAPHIES
        for indicator in CORE_INDICATORS
    ]


def write_completion_overlay(
    official_root: Path,
    output_root: Path,
    *,
    method: str = "backward_fill",
) -> Path:
    official_root = Path(official_root).expanduser().resolve()
    output_root = Path(output_root).expanduser().resolve()
    if method not in {"backward_fill", "forward_fill"}:
        raise CompletionError("unsupported_completion_method")
    verify_release_files(official_root)
    manifest = json.loads((official_root / "manifest.json").read_text(encoding="utf-8"))
    parent_id = str(manifest.get("release_id") or "")
    parent_hash = _sha256(official_root / "manifest.json")
    if not parent_id or manifest.get("contract_id") != "publicdata.indec-eph-labor-state/v1":
        raise CompletionError("official_parent_invalid")
    rows = read_release_observations(official_root)
    index = {(r["period"], r["geography_level"], r["geography_id"], r["indicator_id"]): r for r in rows}
    missing = [key for key in _required_keys() if key not in index]
    output: list[dict[str, str]] = []
    delta = 1 if method == "backward_fill" else -1
    status = "derived_bfill" if method == "backward_fill" else "derived_ffill"
    fill_name = "backward_fill" if method == "backward_fill" else "forward_fill"
    for period, level, geo, indicator in missing:
        source_period = _quarter_offset(period, delta)
        source_key = (source_period, level, geo, indicator)
        source = index.get(source_key)
        if source is None or source.get("value_status") != "observed" or source.get("value") in (None, ""):
            raise CompletionError(f"bounded_source_missing:{period}:{geo}:{indicator}:{source_period}")
        output.append({
            "period": period, "geography_level": level, "geography_id": geo,
            "indicator_id": indicator, "value": source["value"],
            "value_status": status, "fill_method": fill_name,
            "fill_source_period": source_period, "fill_distance_quarters": "1",
            "official_parent_release_id": parent_id,
            "official_parent_manifest_sha256": parent_hash,
            "source_observation_identity": source.get("source_cell_identity", ""),
        })
    if not output:
        raise CompletionError("official_parent_has_no_required_gaps")
    digest = hashlib.sha256(json.dumps(output, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    release_id = f"indec-eph-labor-context-completion-{method}-{digest}"
    destination = output_root / release_id
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    with (destination / "completion.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS); writer.writeheader(); writer.writerows(output)
    file_hash = _sha256(destination / "completion.csv")
    overlay_manifest = {
        "contract": CONTRACT_ID, "release_id": release_id,
        "official_parent_release_id": parent_id,
        "official_parent_manifest_sha256": parent_hash,
        "method": fill_name, "row_count": len(output),
        "files": {"completion.csv": file_hash},
    }
    (destination / "manifest.json").write_text(json.dumps(overlay_manifest, indent=2) + "\n")
    manifest_hash = _sha256(destination / "manifest.json")
    (destination / "checksums.sha256").write_text(
        f"{file_hash}  completion.csv\n{manifest_hash}  manifest.json\n"
    )
    return destination


def validate_completion_overlay(official_root: Path, overlay_root: Path) -> dict:
    official_root = Path(official_root).expanduser().resolve()
    overlay_root = Path(overlay_root).expanduser().resolve()
    verify_release_files(official_root)
    parent_manifest = official_root / "manifest.json"
    parent = json.loads(parent_manifest.read_text(encoding="utf-8"))
    expected_parent_hash = _sha256(parent_manifest)
    manifest = json.loads((overlay_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("contract") != CONTRACT_ID:
        raise CompletionError("completion_contract_invalid")
    if manifest.get("official_parent_release_id") != parent.get("release_id") or manifest.get("official_parent_manifest_sha256") != expected_parent_hash:
        raise CompletionError("completion_parent_identity_mismatch")
    completion = overlay_root / "completion.csv"
    if _sha256(completion) != manifest.get("files", {}).get("completion.csv"):
        raise CompletionError("completion_hash_mismatch")
    official = read_release_observations(official_root)
    official_index = {(r["period"], r["geography_level"], r["geography_id"], r["indicator_id"]): r for r in official}
    rows = list(csv.DictReader(completion.open(encoding="utf-8", newline="")))
    if len(rows) != manifest.get("row_count"):
        raise CompletionError("completion_row_count_mismatch")
    seen = set()
    for row in rows:
        key = (row.get("period", ""), row.get("geography_level", ""), row.get("geography_id", ""), row.get("indicator_id", ""))
        if key in seen or key in official_index:
            raise CompletionError("completion_overwrites_or_duplicates_official_cell")
        seen.add(key)
        if row.get("value_status") not in {"derived_bfill", "derived_ffill"} or row.get("fill_distance_quarters") != "1":
            raise CompletionError("completion_bounds_invalid")
        delta = 1 if row["value_status"] == "derived_bfill" else -1
        if row.get("fill_source_period") != _quarter_offset(row["period"], delta):
            raise CompletionError("completion_source_period_invalid")
        source_key = (row["fill_source_period"], row["geography_level"], row["geography_id"], row["indicator_id"])
        source = official_index.get(source_key)
        if source is None or source.get("value_status") != "observed" or source.get("value") != row.get("value"):
            raise CompletionError("completion_source_not_observed_or_value_mismatch")
        if not row.get("source_observation_identity") or any(row.get(k) for k in ("cv", "ci90_low", "ci90_high", "quality_status")):
            raise CompletionError("completion_quality_metadata_forbidden")
    return {"release_id": manifest["release_id"], "manifest_sha256": _sha256(overlay_root / "manifest.json"), "row_count": len(rows), "rows": rows}
