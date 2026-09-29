from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from .model import SourceDescriptor, SourceSnapshot


SOURCE_CATALOG: dict[str, SourceDescriptor] = {
    "indec_historical_continua": SourceDescriptor(
        source_id="indec_historical_continua",
        url="https://biblioteca.indec.gob.ar/bases/minde/sh_eph_continuasemestral.xls",
        layout_id="indec_historical_matrix_v1",
        kind="rates",
        note="INDEC library historical activity/employment/unemployment/subemployment workbook; retained as an explicit historical source surface.",
    ),
    "indec_rates_2026q2": SourceDescriptor(
        source_id="indec_rates_2026q2",
        url="https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_tasas_indicadores_eph_09_26.xls",
        layout_id="indec_current_matrix_v2",
        kind="rates",
        expected_latest_period="2026-Q2",
        note="Current Mercado de trabajo companion spreadsheet endpoint for the 2026-Q2 publication cycle. L1 must fetch and verify the live binary and layout.",
    ),
    "indec_quality_2026q2": SourceDescriptor(
        source_id="indec_quality_2026q2",
        url="https://www.indec.gob.ar/ftp/cuadros/sociedad/coeficientes_variacion_mdt_09_26.xlsx",
        layout_id="indec_quality_v1",
        kind="quality",
        expected_latest_period="2026-Q2",
        note="CV and 90% confidence-interval companion workbook. INDEC documents this quality surface from 2022-Q4 onward; L1 must verify the live 2026-Q2 snapshot.",
    ),
}

_ALLOWED_HOSTS = {"www.indec.gob.ar", "indec.gob.ar", "biblioteca.indec.gob.ar"}


class SourceError(RuntimeError):
    pass


def validate_official_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise SourceError(f"refusing non-official or non-HTTPS source URL: {url}")


def _requests_transport(url: str, timeout: int) -> tuple[bytes, dict[str, str | None]]:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content, {
        "content_type": response.headers.get("Content-Type"),
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified"),
    }


def fetch_source(source_id: str, output_dir: Path, *, timeout: int = 60, transport=None) -> tuple[Path, Path]:
    if source_id not in SOURCE_CATALOG:
        raise SourceError(f"unknown source_id: {source_id}")
    source = SOURCE_CATALOG[source_id]
    validate_official_url(source.url)
    transport = transport or _requests_transport
    payload, headers = transport(source.url, timeout)
    if not payload:
        raise SourceError(f"empty response for {source.url}")
    sha = hashlib.sha256(payload).hexdigest()
    suffix = Path(urlparse(source.url).path).suffix.lower() or ".bin"
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = output_dir / f"{source.source_id}-{sha[:16]}{suffix}"
    sidecar_path = output_dir / f"{source.source_id}-{sha[:16]}.source.json"
    if snapshot_path.exists() and snapshot_path.read_bytes() != payload:
        raise SourceError(f"immutable snapshot path collision: {snapshot_path}")
    snapshot_path.write_bytes(payload)
    snapshot = SourceSnapshot(
        source_id=source.source_id,
        url=source.url,
        layout_id=source.layout_id,
        kind=source.kind,
        snapshot_path=snapshot_path.name,
        sha256=sha,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        content_type=headers.get("content_type"),
        etag=headers.get("etag"),
        last_modified=headers.get("last_modified"),
    )
    sidecar_path.write_text(json.dumps(asdict(snapshot), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot_path, sidecar_path


def load_snapshot(sidecar_path: Path) -> tuple[SourceSnapshot, Path]:
    raw = json.loads(sidecar_path.read_text(encoding="utf-8"))
    snap = SourceSnapshot(**raw)
    path = sidecar_path.parent / snap.snapshot_path
    if not path.is_file():
        raise SourceError(f"snapshot file declared by sidecar does not exist: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != snap.sha256:
        raise SourceError(f"snapshot checksum mismatch: declared={snap.sha256} actual={actual}")
    validate_official_url(snap.url)
    return snap, path
