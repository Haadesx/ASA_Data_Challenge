# Texas WWC Urbanicity Report

**Dataset:** `raw.wwc_original` in the local Dockerized PostgreSQL environment  
**Source file:** `WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv`  
**Analysis focus:** Texas-coded rows and study-level urbanicity flags

## Executive Summary

Texas-coded WWC findings are heterogeneous across urbanicity buckets, but they do not support a clean rural-versus-urban causal claim. The largest Texas slice is `urban_only` with 871 rows and a mean WWC effect size of about 0.130. The `rural_only` slice shows a much larger mean effect, about 0.356, but it contains only 48 rows. A large overlap bucket (`both`) contains 369 rows where the same finding is tagged as both rural and urban. Another 508 Texas rows are unlabeled on urbanicity.

The main implication is that urbanicity in this dataset behaves more like a noisy moderator than a clean treatment assignment. The strongest numerical effect appears in the small `rural_only` bucket, but the sample is too small and too structurally imbalanced to justify a causal interpretation.

## Core Results

### Texas totals

- All Texas rows: 1,812
- Texas urban rows: 1,240
- Texas rural rows: 417
- Rural-and-urban overlap: 369

### Mean effect sizes

- All Texas: 0.1305
- Texas urban: 0.1250
- Texas rural: 0.1411

### Bucketed urbanicity breakdown

- `urban_only`: 871 rows, mean effect 0.1299
- `unlabeled`: 508 rows, mean effect 0.1171
- `both`: 369 rows, mean effect 0.1160
- `rural_only`: 48 rows, mean effect 0.3563
- `suburban_only`: 16 rows, mean effect 0.2739

## Intervention-Level Caveat

Intervention-level analysis is heavily limited by missing names. Of the 1,812 Texas rows:

- 1,366 rows have missing or blank `i_intervention_name`
- 446 rows have a usable intervention name

That means intervention comparisons should be framed explicitly as "among named intervention rows," not as a full accounting of Texas evidence.

## Named Intervention Signals

Among Texas rows with named interventions and at least 10 rows per intervention-bucket cell:

- `both`:
  - `Leadership and Assistance for Science Education Reform (LASER)`: 72 rows, mean effect 0.0283
  - `Dana Center Mathematics Pathways`: 30 rows, mean effect 0.3043
  - `Investigations in Number, Data, and Space`: 24 rows, mean effect -0.0358
  - `Knowledge is Power Program (KIPP)`: 13 rows, mean effect 0.2345
- `urban_only`:
  - `KIPP`: 28 rows, mean effect 0.1833
  - `Successmaker`: 23 rows, mean effect 0.0214
  - `Enhanced Proactive Reading`: 13 rows, mean effect 0.4255
- `unlabeled`:
  - `Project QUEST`: 25 rows, mean effect 0.1847
  - `Accelerated Math`: 10 rows, mean effect 0.2527

These results show real intervention heterogeneity inside Texas, but the missing-name problem prevents strong ranking claims across the full evidence base.

## Interpretation

The strongest defensible statement is:

> Within Texas-coded WWC rows, urbanicity is heterogeneous rather than cleanly binary. A substantial overlap group exists, a large unlabeled group remains, and the small rural-only slice shows much larger average effect sizes than the dominant urban-only slice.

That is a meaningful descriptive finding. It is not a causal inference result because:

- urbanicity was not randomized
- rural and urban tags overlap
- the rural-only sample is small
- many intervention names are missing

## Reproducibility

Run the saved SQL pack:

```bash
./db/run_query.sh db/queries/texas_urbanicity_eda.sql
```

This report summarizes the outputs from that query file.
