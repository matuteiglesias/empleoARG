import hashlib
import json
from pathlib import Path

import pytest

from empleo_arg.sources import SourceError, fetch_source, load_snapshot, validate_official_url


def test_refuses_non_indec_sources():
    with pytest.raises(SourceError):
        validate_official_url("https://example.com/data.xlsx")
    with pytest.raises(SourceError):
        validate_official_url("http://www.indec.gob.ar/data.xlsx")


def test_fetch_is_immutable_and_sidecar_is_checksummed(tmp_path: Path):
    payload = b"fake-xls-bytes"
    def transport(url, timeout):
        return payload, {"content_type": "application/vnd.ms-excel", "etag": '"x"', "last_modified": None}
    snapshot, sidecar = fetch_source("indec_historical_continua", tmp_path, transport=transport)
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() in sidecar.read_text()
    snap, path = load_snapshot(sidecar)
    assert path == snapshot
    assert snap.source_id == "indec_historical_continua"
