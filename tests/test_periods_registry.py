from empleo_arg.periods import canonical_period, iter_quarters
from empleo_arg.registry import match_geography, match_indicator


def test_period_normalization():
    assert canonical_period("I.17", allowed_styles=("compact_roman",)) == "2017-Q1"
    assert canonical_period("Segundo trimestre de 2026", allowed_styles=("quarter_text",)) == "2026-Q2"
    assert canonical_period("2024-Q1") == "2024-Q1"
    assert len(iter_quarters("2017-Q1", "2026-Q2")) == 38


def test_registry_aliases_are_stable():
    assert match_geography("Región Pampeana").geography_id == "pampeana"
    assert match_geography("Ciudad Autónoma de Buenos Aires").geography_id == "caba"
    assert match_indicator("Tasa de desocupación").indicator_id == "unemployment_rate"
