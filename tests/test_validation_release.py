from decimal import Decimal
from pathlib import Path

import pytest

from empleo_arg.model import Observation, SourceSnapshot
from empleo_arg.release import verify_release_files, write_release
from empleo_arg.validation import EXCEPTION_FLAGS, ValidationError, apply_exception_flags, coverage_ledger, validate_observations


def obs(period="2020-Q2", geo_level="region", geo="pampeana", indicator="unemployment_rate", value=Decimal("9.1")):
    labels={"pampeana":"Pampeana","total_31_agglomerates":"Total 31 aglomerados urbanos"}
    return Observation(period, geo_level, geo, labels[geo], indicator, "Tasa de desocupación", value, "percent", "desocupados", "PEA", "fixture", "2026-09", "a"*64, "Sheet!R1C1", "observed")


def test_exception_flags_are_metadata_only():
    row = obs(); original = row.value
    apply_exception_flags([row])
    assert row.exception_flags == ["pandemic_fieldwork_regime"]
    assert row.value == original


def test_duplicate_normalized_cell_fails():
    row = obs()
    with pytest.raises(ValidationError):
        validate_observations([row, obs()])


def test_coverage_ledger_has_expected_grid_and_gaps():
    ledger = coverage_ledger([obs()])
    assert len(ledger) == 38 * 7 * 4
    assert sum(r["coverage_status"] == "present" for r in ledger) == 1


def test_release_is_immutable_and_checksum_verified(tmp_path: Path):
    row = obs(period="2017-Q1")
    snapshot = SourceSnapshot("fixture", "https://www.indec.gob.ar/x.xls", "indec_current_matrix_v2", "rates", "x.xls", "a"*64, "2026-09-29T00:00:00+00:00")
    release = write_release(tmp_path, [row], [snapshot])
    verify_release_files(release)
    with pytest.raises(FileExistsError):
        write_release(tmp_path, [row], [snapshot])
    (release / "coverage.csv").write_text("tamper", encoding="utf-8")
    with pytest.raises(RuntimeError):
        verify_release_files(release)
