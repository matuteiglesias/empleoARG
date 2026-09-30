# L1B — bounded labor-context completion for documented official gaps

Status: local execution policy, 2026-09-29.

## Motivation

The real L1 gate found one genuine official-data hole:

```text
2019-Q3
region = noreste
indicators = activity_rate, employment_rate, unemployment_rate, subemployment_rate
```

INDEC did not publish the NEA regional values because Gran Resistencia was excluded from EPH fieldwork in that quarter.

The canonical official product must preserve that fact.

Do **not** rewrite `publicdata.indec-eph-labor-state/v1` as if those four cells were observed.

## Policy

Create a separately identified **model-ready completion overlay** containing only derived values needed to make the longitudinal labor-context surface usable.

Contract, conceptually:

```text
research.indec-eph-labor-context-completion/v1
```

The centerline completion rule is intentionally simple:

```text
group by geography_level + geography_id + indicator_id
sort by period
backward-fill value
maximum gap = 1 quarter
```

For the current real data this means exactly:

```text
2019-Q3 / noreste / each core indicator
    <- 2019-Q4 / noreste / same indicator
```

No other cell may be filled unless a future policy revision explicitly authorizes it.

## Guardrails

The completion overlay must:

- bind the exact incomplete official C1 release ID and manifest SHA-256;
- contain only cells absent from the official required grid;
- never overwrite an observed official value;
- fill only within the same geography and same indicator;
- require the source cell to be exactly one quarter later;
- fail if more than one quarter is missing;
- fail if the next-quarter source cell is absent/non-observed;
- never fill CV, CI, quality status or publication metadata as if source-backed;
- mark every derived cell explicitly.

Minimum derived-row metadata:

```text
period
geography_level
geography_id
indicator_id
value
value_status = derived_bfill
fill_method = backward_fill
fill_source_period
fill_distance_quarters
official_parent_release_id
official_parent_manifest_sha256
source_observation_identity
```

The official parent remains the source of geography/indicator semantics.

## Model-consumption semantics

The longitudinal welfare runtime may consume:

```text
official C1 observations
+
explicit L1B completion overlay
```

and must persist both parent identities.

A run with a completion overlay is still measurement-mode, not forecast/nowcast. The filled value is retrospective derived context and must never be described as an official 2019-Q3 NEA estimate.

## Sensitivity

Because the gap is only one region-quarter, run a bounded sensitivity for the L10 commission:

1. centerline: backward-fill from 2019-Q4;
2. sensitivity: forward-fill from 2019-Q2.

Optionally also report a linear midpoint sensitivity if trivial.

Compare at least:

- 2019-Q3 person predictions in NEA;
- 2019-Q3 household predictions in NEA;
- national aggregate welfare summaries;
- fitted labor-context contribution / terminal metrics.

If the difference is negligible, retain backward-fill as the simple deterministic centerline.

Do not turn this into a general imputation search.

## L1 completion status

L1 source acquisition should be reported as:

```text
official coverage: 1060 / 1064
documented official gap: 4 cells
official release: valid but structurally incomplete
model-ready completion: supplied by L1B overlay
```

This is sufficient to unblock longitudinal model commissioning once the downstream consumer validates the overlay.

## Non-goals

- no fabrication of official observations;
- no quality/CV/CI imputation;
- no multi-quarter filling;
- no cross-region borrowing;
- no stochastic imputation;
- no forecasting.
