#!/usr/bin/env python3
"""Verify the committed employment-series cutoff without network access."""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
status = json.loads((ROOT / "DATA_STATUS.json").read_text(encoding="utf-8"))
artifact = ROOT / status["artifact"]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


if not artifact.is_file():
    fail(f"missing declared artifact: {artifact.relative_to(ROOT)}")

with artifact.open(newline="", encoding="utf-8") as handle:
    reader = csv.reader(handle)
    header = next(reader, None)
    rows = list(reader)

if not header or not rows:
    fail("artifact is empty")
if any(len(row) != len(header) + 1 for row in rows):
    fail("row width does not match one date index plus the named series columns")

periods = []
for row in rows:
    try:
        periods.append(date.fromisoformat(row[0]))
    except (IndexError, ValueError) as exc:
        fail(f"invalid first-column period in row {row!r}: {exc}")

actual_max = max(periods).isoformat()
if actual_max != status["artifact_max_period"]:
    fail(
        "declared artifact_max_period does not match CSV: "
        f"declared={status['artifact_max_period']} actual={actual_max}"
    )

print(
    json.dumps(
        {
            "artifact": status["artifact"],
            "rows": len(rows),
            "series_columns": len(header),
            "first_period": min(periods).isoformat(),
            "artifact_max_period": actual_max,
            "automation_configured_in_repository": status["automation"]["configured_in_repository"],
            "result": "snapshot declaration matches committed artifact",
        },
        indent=2,
    )
)
