import hashlib
from pathlib import Path

import pytest
from openpyxl import Workbook

from empleo_arg.model import SourceSnapshot
from empleo_arg.parser import SchemaDriftError, parse_quality_workbook, parse_rate_workbook


def snap(path: Path, *, layout="indec_current_matrix_v2", kind="rates"):
    return SourceSnapshot(
        source_id="fixture", url="https://www.indec.gob.ar/ftp/cuadros/sociedad/fixture_09_26.xlsx",
        layout_id=layout, kind=kind, snapshot_path=path.name,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), retrieved_at="2026-09-29T00:00:00+00:00",
    )


def test_parse_current_matrix_and_missing_marker(tmp_path: Path):
    p = tmp_path / "rates.xlsx"
    wb = Workbook(); ws = wb.active; ws.title = "Tasas"
    for title, a, b in [
        ("Tasa de actividad", 48.1, 48.4),
        ("Tasa de empleo", 44.0, 44.2),
        ("Tasa de desocupación", 8.5, "s/d"),
        ("Tasa de subocupación", 11.2, 11.0),
    ]:
        ws.append([title]); ws.append(["Período", "Total 31 aglomerados urbanos", "Gran Buenos Aires", "Cuyo", "Noreste", "Noroeste", "Pampeana", "Patagonia"])
        ws.append(["Primer trimestre de 2026", a, a, a, a, a, a, a])
        ws.append(["Segundo trimestre de 2026", b, b, b, b, b, b, b]); ws.append([])
    wb.save(p)
    obs = parse_rate_workbook(p, snap(p))
    assert len(obs) == 4 * 2 * 7
    assert len({o.key for o in obs}) == len(obs)
    assert any(o.period == "2026-Q2" and o.indicator_id == "unemployment_rate" and o.value_status == "missing_source" for o in obs)
    assert any(o.geography_id == "patagonia" and o.indicator_id == "activity_rate" for o in obs)


def test_parse_quality_fixture(tmp_path: Path):
    p = tmp_path / "quality.xlsx"
    wb = Workbook(); ws = wb.active
    ws.append(["Tasa de desocupación - Cuarto trimestre de 2022"])
    ws.append(["Aglomerado", "CV", "Límite inferior 90%", "Límite superior 90%"])
    ws.append(["Gran La Plata", 0.12, 5.1, 7.9])
    wb.save(p)
    recs = parse_quality_workbook(p, snap(p, layout="indec_quality_v1", kind="quality"))
    assert recs[0].period == "2022-Q4"
    assert recs[0].geography_id == "gran_la_plata"
    assert str(recs[0].cv) == "0.12"


def test_unknown_layout_fails_closed(tmp_path: Path):
    p = tmp_path / "drift.xlsx"; wb = Workbook(); wb.save(p)
    with pytest.raises(SchemaDriftError):
        parse_rate_workbook(p, snap(p, layout="unknown_layout"))


def test_parse_wide_official_quarter_matrix(tmp_path: Path):
    p = tmp_path / "wide.xlsx"
    wb = Workbook(); ws = wb.active; ws.title = "Cuadro 1.1"
    ws.append(["Principales indicadores"])
    ws.append([None, "Total 31 aglomerados urbanos"])
    ws.append([None, "Año 2026", None, None])
    ws.append([None, "1° trimestre", "2° trimestre", None])
    ws.append([])
    ws.append(["Actividad", 48.0, 49.0])
    ws.append(["Empleo", 44.0, 45.0])
    ws.append(["Desocupación abierta", 8.0, 7.9])
    ws.append(["Subocupación", 11.0, 11.5])
    wb.save(p)
    obs = parse_rate_workbook(p, snap(p))
    assert len(obs) == 8
    assert {o.period for o in obs} == {"2026-Q1", "2026-Q2"}
    assert {o.indicator_id for o in obs} == {
        "activity_rate", "employment_rate", "unemployment_rate", "subemployment_rate"
    }
