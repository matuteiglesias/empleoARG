# L1 — real canonical labor-state release gate

Status: local-data execution packet, 2026-09-29.

## Purpose

Execute the real-data gate after merged C1.

Authoritative architecture remains:

`docs/CANONICAL_LABOR_STATE_2017_CURRENT_PLAN.md`

C1 implemented the governed contract `publicdata.indec-eph-labor-state/v1`. L1 must now prove that contract against the actual official INDEC binary sources and produce the first immutable real release.

This is a **local/data-access task**, not a cloud architecture task.

## Required real coverage

Target:

```text
2017-Q1 .. 2026-Q2
```

Required model-critical grid:

```text
38 quarters
× (total 31 agglomerates + 6 regions)
× 4 principal indicators
= 1,064 required cells
```

Principal indicators:

- activity rate;
- employment rate;
- unemployment rate;
- subemployment rate.

Retain supported individual-agglomerate observations as additional product rows.

## Inputs

Use the merged C1 implementation on `main`.

Prefer the official INDEC structured source descriptors already registered by C1. Fetch the actual XLS/XLSX binaries locally and persist exact source receipts/hashes outside the checkout.

Suggested roots:

```text
/home/matias/data/labor-state-sources/
/home/matias/data/labor-state-releases/
```

Do not replace the committed historical CSV snapshots.

## Execution

1. Fetch every required official source binary.
2. Record final resolved URL, local filename, bytes and SHA-256.
3. Verify actual workbook/tab/layout topology against the C1 declared parser layouts.
4. If real schema differs, fix the smallest explicit parser/layout declaration in this repo; do not add heuristic silent fallback.
5. Build the normalized release.
6. Validate the complete 1,064-cell required grid.
7. Verify total-31 and six-region identity mappings.
8. Verify the actual historical/current source transition boundary.
9. Verify the real CV / 90% CI availability boundary and attach quality values only where official source evidence exists.
10. Compare overlapping official values against the old committed snapshot and explain every discrepancy class.
11. Verify exception metadata:
   - `2020-Q2 pandemic_fieldwork_regime`
   - `2024-Q1 2024_h1_macroeconomic_shock`
   - `2024-Q2 2024_h1_macroeconomic_shock`
12. Run release validation and checksum-tamper checks.

No interpolation, smoothing, nearest-period substitution, forward fill or inferred confidence intervals.

## Receipt

Persist a compact local receipt containing at least:

```text
release_id
release_path
manifest_sha256
source_receipts
coverage_summary
latest_period
schema_transition_summary
quality_boundary_summary
legacy_overlap_summary
exception_period_check
validation_commands
validation_results
```

If any required official cell is genuinely unavailable, stop with an explicit bounded failure rather than weakening the coverage gate.

## Definition of done

L1 is complete when one immutable real `publicdata.indec-eph-labor-state/v1` release for 2017-Q1..2026-Q2 passes validation and is ready for exact consumption by `encuestador-de-hogares`.

## Non-goals

- no welfare model;
- no individual labor probabilities;
- no KL anchoring;
- no forecast/nowcast;
- no Census work.
