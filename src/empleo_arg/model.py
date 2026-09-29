from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    url: str
    layout_id: str
    kind: str
    expected_latest_period: str | None = None
    note: str = ""


@dataclass(frozen=True)
class SourceSnapshot:
    source_id: str
    url: str
    layout_id: str
    kind: str
    snapshot_path: str
    sha256: str
    retrieved_at: str
    content_type: str | None = None
    etag: str | None = None
    last_modified: str | None = None


@dataclass
class Observation:
    period: str
    geography_level: str
    geography_id: str
    geography_label: str
    indicator_id: str
    indicator_label: str
    value: Decimal | None
    unit: str
    numerator_universe: str
    denominator_universe: str
    source_id: str
    source_publication_date: str | None
    source_snapshot_sha256: str
    source_cell_identity: str
    value_status: str
    quality_status: str = "not_available"
    cv: Decimal | None = None
    ci90_low: Decimal | None = None
    ci90_high: Decimal | None = None
    exception_flags: list[str] = field(default_factory=list)
    source_geography_code: str | None = None
    source_geography_label: str | None = None
    quality_source_id: str | None = None
    quality_source_snapshot_sha256: str | None = None
    quality_source_cell_identity: str | None = None

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (self.period, self.geography_level, self.geography_id, self.indicator_id)


@dataclass(frozen=True)
class QualityRecord:
    period: str
    geography_id: str
    indicator_id: str
    cv: Decimal | None
    ci90_low: Decimal | None
    ci90_high: Decimal | None
    source_id: str
    source_snapshot_sha256: str
    source_cell_identity: str


@dataclass(frozen=True)
class Geography:
    geography_level: str
    geography_id: str
    geography_label: str
    aliases: tuple[str, ...]
    source_code: str | None = None


@dataclass(frozen=True)
class Indicator:
    indicator_id: str
    indicator_label: str
    aliases: tuple[str, ...]
    unit: str
    numerator_universe: str
    denominator_universe: str


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip().replace("%", "").replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None
