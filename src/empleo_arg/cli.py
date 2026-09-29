from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from .model import Observation
from .parser import parse_quality_workbook, parse_rate_workbook
from .release import read_release_observations, verify_release_files, write_release
from .sources import SOURCE_CATALOG, fetch_source, load_snapshot
from .validation import apply_exception_flags, assert_required_coverage, attach_quality, coverage_ledger, validate_observations


def _parse_release_rows(release_dir: Path) -> list[Observation]:
    rows = read_release_observations(release_dir)
    out = []
    for row in rows:
        out.append(Observation(
            period=row["period"], geography_level=row["geography_level"], geography_id=row["geography_id"], geography_label=row["geography_label"],
            indicator_id=row["indicator_id"], indicator_label=row["indicator_label"], value=Decimal(row["value"]) if row["value"] else None,
            unit=row["unit"], numerator_universe=row["numerator_universe"], denominator_universe=row["denominator_universe"], source_id=row["source_id"],
            source_publication_date=row["source_publication_date"] or None, source_snapshot_sha256=row["source_snapshot_sha256"], source_cell_identity=row["source_cell_identity"],
            value_status=row["value_status"], quality_status=row["quality_status"], cv=Decimal(row["cv"]) if row["cv"] else None,
            ci90_low=Decimal(row["ci90_low"]) if row["ci90_low"] else None, ci90_high=Decimal(row["ci90_high"]) if row["ci90_high"] else None,
            exception_flags=json.loads(row["exception_flags"] or "[]"), source_geography_code=row["source_geography_code"] or None,
            source_geography_label=row["source_geography_label"] or None, quality_source_id=row["quality_source_id"] or None,
            quality_source_snapshot_sha256=row["quality_source_snapshot_sha256"] or None, quality_source_cell_identity=row["quality_source_cell_identity"] or None,
        ))
    return out


def cmd_sources(_: argparse.Namespace) -> int:
    print(json.dumps([asdict(s) for s in SOURCE_CATALOG.values()], indent=2, ensure_ascii=False))
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    snapshot, sidecar = fetch_source(args.source_id, Path(args.output_dir), timeout=args.timeout)
    print(json.dumps({"snapshot": str(snapshot), "sidecar": str(sidecar)}, indent=2))
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    rate_snaps = [load_snapshot(Path(p)) for p in args.rates_source]
    observations = []
    for snap, path in rate_snaps:
        observations.extend(parse_rate_workbook(path, snap))
    quality_records = []
    quality_snaps = []
    for p in args.quality_source or []:
        snap, path = load_snapshot(Path(p)); quality_snaps.append((snap, path)); quality_records.extend(parse_quality_workbook(path, snap))
    apply_exception_flags(observations)
    attach_quality(observations, quality_records)
    validate_observations(observations)
    release = write_release(Path(args.output_root), observations, [s for s, _ in rate_snaps + quality_snaps])
    print(release)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    release = Path(args.release)
    verify_release_files(release)
    observations = _parse_release_rows(release)
    validate_observations(observations)
    ledger = coverage_ledger(observations)
    if args.require_full_coverage:
        assert_required_coverage(ledger)
    print(json.dumps({"release": str(release), "rows": len(observations), "required_cells": len(ledger), "missing_required": sum(r["coverage_status"] != "present" for r in ledger), "result": "PASS"}, indent=2))
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    observations = _parse_release_rows(Path(args.release))
    ledger = coverage_ledger(observations)
    writer = csv.DictWriter(__import__("sys").stdout, fieldnames=["period", "geography_level", "geography_id", "indicator_id", "coverage_status"])
    writer.writeheader(); writer.writerows(ledger)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="empleo-arg")
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sources", help="list pinned official source descriptors"); s.set_defaults(func=cmd_sources)
    s = sub.add_parser("fetch", help="fetch one immutable official INDEC source snapshot")
    s.add_argument("source_id", choices=sorted(SOURCE_CATALOG)); s.add_argument("--output-dir", required=True); s.add_argument("--timeout", type=int, default=60); s.set_defaults(func=cmd_fetch)
    s = sub.add_parser("build", help="build an immutable normalized release from fetched source sidecars")
    s.add_argument("--rates-source", action="append", required=True, help=".source.json from fetch; repeatable")
    s.add_argument("--quality-source", action="append", help="quality .source.json from fetch; repeatable")
    s.add_argument("--output-root", required=True); s.set_defaults(func=cmd_build)
    s = sub.add_parser("validate", help="verify checksums, schema, duplicates and optional required coverage")
    s.add_argument("release"); s.add_argument("--require-full-coverage", action="store_true"); s.set_defaults(func=cmd_validate)
    s = sub.add_parser("coverage", help="emit 2017-Q1..2026-Q2 required coverage ledger")
    s.add_argument("release"); s.set_defaults(func=cmd_coverage)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
