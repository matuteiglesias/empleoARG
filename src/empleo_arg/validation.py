from __future__ import annotations

from collections import Counter
from decimal import Decimal

from .model import Observation, QualityRecord
from .periods import iter_quarters
from .registry import CORE_INDICATORS, GEO_BY_ID, INDICATOR_BY_ID, REQUIRED_GEOGRAPHIES

EXCEPTION_FLAGS = {
    "2020-Q2": ["pandemic_fieldwork_regime"],
    "2024-Q1": ["2024_h1_macroeconomic_shock"],
    "2024-Q2": ["2024_h1_macroeconomic_shock"],
}

QUALITY_PUBLICATION_START = "2022-Q4"


class ValidationError(RuntimeError):
    pass


def apply_exception_flags(observations: list[Observation]) -> None:
    for obs in observations:
        obs.exception_flags = list(EXCEPTION_FLAGS.get(obs.period, ()))


def attach_quality(observations: list[Observation], quality: list[QualityRecord]) -> None:
    qmap: dict[tuple[str, str, str], QualityRecord] = {}
    for q in quality:
        key = (q.period, q.geography_id, q.indicator_id)
        if key in qmap:
            raise ValidationError(f"duplicate quality cell: {key}")
        qmap[key] = q
    for obs in observations:
        q = qmap.get((obs.period, obs.geography_id, obs.indicator_id))
        if q:
            obs.cv = q.cv
            obs.ci90_low = q.ci90_low
            obs.ci90_high = q.ci90_high
            obs.quality_status = "source_backed"
            obs.quality_source_id = q.source_id
            obs.quality_source_snapshot_sha256 = q.source_snapshot_sha256
            obs.quality_source_cell_identity = q.source_cell_identity
        elif obs.period < QUALITY_PUBLICATION_START:
            obs.quality_status = "not_published"
        else:
            obs.quality_status = "not_attached"


def validate_observations(observations: list[Observation]) -> None:
    if not observations:
        raise ValidationError("no observations")
    counts = Counter(obs.key for obs in observations)
    dups = [k for k, n in counts.items() if n > 1]
    if dups:
        raise ValidationError(f"duplicate normalized cells ({len(dups)}): {dups[:5]}")
    for obs in observations:
        if obs.geography_id not in GEO_BY_ID:
            raise ValidationError(f"unknown geography_id: {obs.geography_id}")
        if obs.indicator_id not in INDICATOR_BY_ID:
            raise ValidationError(f"unknown indicator_id: {obs.indicator_id}")
        if obs.value_status == "observed" and obs.value is None:
            raise ValidationError(f"observed cell lacks value: {obs.key}")
        if obs.value_status != "observed" and obs.value is not None:
            raise ValidationError(f"non-observed cell unexpectedly carries a value: {obs.key}")
        if obs.value is not None and not (Decimal("0") <= obs.value <= Decimal("100")):
            raise ValidationError(f"rate outside [0,100] published scale: {obs.key}={obs.value}")
        if obs.quality_status == "source_backed" and obs.cv is None and obs.ci90_low is None and obs.ci90_high is None:
            raise ValidationError(f"source_backed quality row has no quality values: {obs.key}")


def coverage_ledger(observations: list[Observation], start: str = "2017-Q1", end: str = "2026-Q2") -> list[dict[str, str]]:
    index = {obs.key: obs for obs in observations}
    rows = []
    for period in iter_quarters(start, end):
        for geo_id in REQUIRED_GEOGRAPHIES:
            geo = GEO_BY_ID[geo_id]
            for indicator_id in CORE_INDICATORS:
                key = (period, geo.geography_level, geo_id, indicator_id)
                obs = index.get(key)
                if obs is None:
                    status = "missing_observation"
                elif obs.value_status == "observed":
                    status = "present"
                else:
                    status = obs.value_status
                rows.append({
                    "period": period,
                    "geography_level": geo.geography_level,
                    "geography_id": geo_id,
                    "indicator_id": indicator_id,
                    "coverage_status": status,
                })
    return rows


def assert_required_coverage(ledger: list[dict[str, str]]) -> None:
    missing = [row for row in ledger if row["coverage_status"] != "present"]
    if missing:
        sample = missing[:10]
        raise ValidationError(f"required coverage incomplete: {len(missing)} cells not present; sample={sample}")
