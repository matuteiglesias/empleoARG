# Canonical EPH labor-state product — implementation plan

Status: implementation-ready design, 2026-09-29.

## Mission

Revive `empleoARG` as the public-data authority for **official INDEC EPH labor-market state by period and geography**. Preserve the historical snapshot as evidence, but do not extend the old opaque Ministry-of-Economy workbook pipeline as the new authority.

The target artifact is conceptually:

```text
publicdata.indec-eph-labor-state/v1
```

This product is an observed aggregate context surface. It does **not** assign current labor states to individual Census persons, estimate welfare, or calibrate latent person states.

## Source strategy

Use direct official INDEC material.

Primary evidence already verified during planning:

- INDEC publishes a historical download for activity, employment, unemployment and subemployment by regions and agglomerates from the EPH continua series.
- Current `Mercado de trabajo. Tasas e indicadores socioeconómicos (EPH)` releases publish total-31-agglomerates, six-region and agglomerate tables.
- As of 2026-09-29, the latest labor measurement is 2026-Q2; the EPH microdata surface is only through 2026-Q1.
- INDEC publishes CV / 90% confidence-interval files for principal labor indicators from 2022-Q4 onward.
- EPH 2020-Q2 is an exceptional COVID fieldwork quarter; 2024-Q1 and 2024-Q2 are separate 2024-H1 macroeconomic shock quarters for this research program. All three must remain explicitly marked rather than silently normalized away.

Prefer machine-readable official XLS/XLSX downloads. PDF tables are evidence/fallback, not the preferred ingestion surface.

## Product grain

One normalized row per:

```text
period
geography_level
geography_id
indicator_id
```

Minimum fields:

```text
period                    # YYYY-QN
geography_level           # total_31 | region | agglomerate
geography_id              # stable repo-owned normalized id
geography_label
indicator_id
indicator_label
value
unit
numerator_universe
denominator_universe
source_id
source_publication_date
source_snapshot_sha256
source_cell_identity
value_status
quality_status
cv
ci90_low
ci90_high
exception_flags
```

Do not fabricate CV/CI fields for periods where INDEC did not publish them.

## Stable geography

The centerline consumer needs these six region IDs:

```text
gran_buenos_aires
cuyo
noreste
noroeste
pampeana
patagonia
```

Also retain `total_31_agglomerates`.

Persist individual agglomerates in the public-data product where the official source supports them, but they are not required by the first welfare-model centerline. Keep source agglomerate codes and labels alongside normalized IDs.

## Indicator policy

Acquire and preserve all clearly defined official principal labor indicators exposed by the chosen source. The first model-facing stable subset is:

```text
activity_rate
employment_rate
unemployment_rate
subemployment_rate
```

Also preserve, when homogeneous and source-backed, demand-pressure measures such as occupied job seekers and demanding/non-demanding subemployment.

The downstream L10 model should initially avoid feeding algebraically redundant rates indiscriminately. A compact candidate state is:

```text
activity_rate
unemployment_rate
subemployment_rate
```

with employment retained in the product and available for sensitivity work.

## Derived consumer view

The public artifact owns official observations, not ML feature engineering. It may nevertheless provide a deterministic convenience view or documented recipe for:

```text
national indicator at t
regional deviation = regional indicator(g,t) - national indicator(t)
```

The welfare repo may own the final model feature materialization.

## Coverage gate

Required real coverage for the immediate longitudinal study:

```text
2017-Q1 .. 2026-Q2
```

The release must emit a coverage ledger over every expected period × required geography × core indicator.

No forward/back fill. Missing official observations remain missing with explicit status.

## Exceptional shock periods

Preserve all official observations exactly. Add explicit research metadata for:

```text
2020-Q2  pandemic_fieldwork_regime
2024-Q1  2024_h1_macroeconomic_shock
2024-Q2  2024_h1_macroeconomic_shock
```

These flags are metadata for downstream structural modeling. They do not modify, smooth, replace or reinterpret the official published labor values.

## Repository boundary

Add / refresh `SYSTEM.yaml` during implementation so this repository clearly owns:

- official labor-series acquisition/normalization and release lineage;
- stable labor indicator/geography identities;
- source/quality metadata and coverage QA.

It must explicitly not own:

- EPH person microdata;
- person-level employment imputation;
- Census transport;
- welfare or poverty modeling.

The existing `datos/45.2_ECTDT.csv` and `datos/42.3_EPH_PUNTUA.csv` remain historical snapshots and must not be silently overwritten and called current.

## Cloud work packet — C1

Implement the canonical source adapter and release contract.

Deliver:

1. source-discovery/fetch layer pinned to official INDEC endpoints;
2. parser(s) for the chosen historical/current official spreadsheet surfaces;
3. stable geography and indicator registries;
4. normalized artifact writer + manifest/checksums;
5. coverage and duplicate-cell validators;
6. quality/CV/CI attachment where source-backed;
7. exceptional-period metadata for 2020-Q2 and 2024-Q1/Q2;
8. fixture tests and synthetic drift/failure tests;
9. `SYSTEM.yaml`, README and command surface;
10. a network-independent test suite.

Do not scrape values out of prose when a structured official table exists.

Suggested commands:

```text
empleo-arg fetch ...
empleo-arg build ...
empleo-arg validate <release>
empleo-arg coverage <release>
```

Names may differ; the contract matters more than CLI spelling.

## Local work packet — L1

Run the real-data gate after C1 lands.

Materialize outside the checkout, for example:

```text
/home/matias/data/labor-state-sources/
/home/matias/data/labor-state-releases/
```

Required receipt:

- exact source URLs/files and hashes;
- 2017-Q1..2026-Q2 coverage matrix;
- six regions + total-31 coverage;
- core indicator coverage;
- latest period = 2026-Q2;
- any source revisions/schema transitions;
- 2020-Q2 and 2024-Q1/Q2 flagged with distinct exception reasons;
- CV/CI availability beginning at the actual source boundary;
- comparison against the old committed series on overlapping periods, with differences explained rather than overwritten.

## Definition of done

This work packet is complete when one immutable, validated real release can be consumed by `encuestador-de-hogares` without importing `empleoARG` runtime code, and when the old 2023-cutoff snapshot is no longer the only machine-readable labor surface in this repository.

## Non-goals

- no nowcasting;
- no forecast beyond latest official labor quarter;
- no person-level `CONDACT`;
- no latent-state KL calibration;
- no income or poverty estimation.
