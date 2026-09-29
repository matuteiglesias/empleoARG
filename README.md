# Empleo Argentina — estado laboral oficial EPH

`empleoARG` is being revived as the governed public-data authority for **official INDEC EPH labor-market state by quarter and geography**. The canonical contract is:

```text
publicdata.indec-eph-labor-state/v1
```

The old committed CSVs remain historical evidence. They are not overwritten or relabeled as the current product.

## System boundary

This repository owns official source acquisition, source snapshots and hashes, stable labor indicator/geography identities, normalization, source-backed quality metadata, coverage QA, and immutable release construction. It does **not** own EPH person microdata, person-level employment imputation, Census transport, latent-state calibration, income modeling, or poverty estimation. See `SYSTEM.yaml` and `docs/CANONICAL_LABOR_STATE_2017_CURRENT_PLAN.md`.

## Canonical product grain

One row per:

```text
period × geography_level × geography_id × indicator_id
```

The first model-critical geography set is total 31 agglomerates plus the six standard EPH regions. Supported official agglomerate rows are retained too. Core indicators are activity, employment, unemployment, and subemployment rates; clearly defined demand-pressure measures are retained when present in the official workbook.

Official values are preserved on their published scale. There is no interpolation, forward/back filling, smoothing, or person-level inference.

Exceptional quarters are metadata only:

- `2020-Q2` → `pandemic_fieldwork_regime`
- `2024-Q1` → `2024_h1_macroeconomic_shock`
- `2024-Q2` → `2024_h1_macroeconomic_shock`

## Official source surfaces

The source catalog is executable:

```bash
empleo-arg sources
```

It separates explicit layouts instead of silently adapting column positions:

- INDEC library historical EPH Continua workbook: `sh_eph_continuasemestral.xls`;
- current `Mercado de trabajo. Tasas e indicadores socioeconómicos (EPH)` companion XLS;
- source-backed CV / 90% confidence-interval XLSX, documented by INDEC from 2022-Q4 onward.

The 2026-Q2 endpoint descriptors are pinned in the catalog, but a real release is **not** claimed by this code change. The L1 gate must fetch and validate the live binaries, source hashes, schema, and complete 2017-Q1..2026-Q2 coverage.

## Commands

Create immutable source snapshots outside the checkout:

```bash
empleo-arg fetch indec_rates_2026q2 --output-dir /home/matias/data/labor-state-sources
empleo-arg fetch indec_quality_2026q2 --output-dir /home/matias/data/labor-state-sources
```

Build from the resulting `.source.json` receipts:

```bash
empleo-arg build \
  --rates-source /home/matias/data/labor-state-sources/<rates>.source.json \
  --quality-source /home/matias/data/labor-state-sources/<quality>.source.json \
  --output-root /home/matias/data/labor-state-releases
```

Validate an immutable release and require the model-critical coverage gate:

```bash
empleo-arg validate /home/matias/data/labor-state-releases/<release-id> --require-full-coverage
empleo-arg coverage /home/matias/data/labor-state-releases/<release-id>
```

A release contains `labor_state.csv`, `coverage.csv`, stable registries, `manifest.json`, and `checksums.sha256`. Unknown spreadsheet layouts fail closed with a schema-drift error; the parser does not guess new column positions.

## Offline tests

Network-dependent acquisition is deliberately separate from tests:

```bash
python -m pip install -e '.[test]'
pytest -q
python scripts/verify_snapshot.py
```

Tests synthesize workbook fixtures locally and cover known layouts, source URL policy, duplicate cells, coverage gaps, exceptional metadata, immutable release checksums, and drift failures.

## Historical snapshot

The previous Ministry-of-Economy workbook pipeline is preserved as evidence:

- `Descargador de Datos Oficiales.ipynb`
- `datos/apendice3a.xlsx`
- `datos/42.3_EPH_PUNTUA.csv`
- `datos/45.2_ECTDT.csv`
- `DATA_STATUS.json`

Its declared cutoff remains independently checkable with:

```bash
python scripts/verify_snapshot.py
```

Do not describe those legacy CSVs as the current official labor-state product.
