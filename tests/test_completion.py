import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from empleo_arg import completion
from empleo_arg.completion import CompletionError, validate_completion_overlay, write_completion_overlay
from empleo_arg.model import Observation, SourceSnapshot
from empleo_arg.release import write_release


def _observation(period: str, value: str) -> Observation:
    return Observation(
        period, "region", "noreste", "Noreste", "activity_rate", "Tasa de actividad",
        Decimal(value), "percent", "pea", "total", "fixture", None, "a" * 64,
        f"fixture!{period}", "observed",
    )


def _parent(tmp_path: Path) -> Path:
    snapshot = SourceSnapshot("fixture", "https://www.indec.gob.ar/fixture.xls", "indec_current_matrix_v2", "rates", "fixture.xls", "a" * 64, "2026-09-29T00:00:00Z")
    return write_release(tmp_path / "parent", [_observation("2019-Q2", "40"), _observation("2019-Q4", "42")], [snapshot])


def test_bounded_completion_and_parent_binding(tmp_path, monkeypatch):
    monkeypatch.setattr(completion, "_required_keys", lambda: [("2019-Q3", "region", "noreste", "activity_rate")])
    parent = _parent(tmp_path)
    overlay = write_completion_overlay(parent, tmp_path / "overlays")
    result = validate_completion_overlay(parent, overlay)
    assert result["row_count"] == 1
    row = result["rows"][0]
    assert row["value_status"] == "derived_bfill"
    assert row["fill_source_period"] == "2019-Q4"
    assert row["fill_distance_quarters"] == "1"


def test_overlay_parent_hash_mismatch_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(completion, "_required_keys", lambda: [("2019-Q3", "region", "noreste", "activity_rate")])
    parent = _parent(tmp_path)
    overlay = write_completion_overlay(parent, tmp_path / "overlays")
    manifest_path = overlay / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["official_parent_manifest_sha256"] = "b" * 64
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(CompletionError, match="parent_identity"):
        validate_completion_overlay(parent, overlay)


@pytest.mark.parametrize("field,value", [
    ("fill_source_period", "2019-Q1"),
    ("geography_id", "cuyo"),
    ("indicator_id", "employment_rate"),
])
def test_completion_bounds_reject_bad_source(tmp_path, monkeypatch, field, value):
    monkeypatch.setattr(completion, "_required_keys", lambda: [("2019-Q3", "region", "noreste", "activity_rate")])
    parent = _parent(tmp_path)
    overlay = write_completion_overlay(parent, tmp_path / "overlays")
    path = overlay / "completion.csv"
    rows = list(csv.DictReader(path.open()))
    rows[0][field] = value
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    manifest = json.loads((overlay / "manifest.json").read_text())
    manifest["files"]["completion.csv"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (overlay / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(CompletionError):
        validate_completion_overlay(parent, overlay)
