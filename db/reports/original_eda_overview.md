# Original WWC Dataset Overview

**Source table:** `raw.wwc_original`  
**Scope:** original WWC export only, no teammate-aggregated data  
**Run date:** March 20, 2026

## What this EDA is for

This report gives a structural overview of the original WWC table so downstream analysis can use the right grain, the right metrics, and the right caveats. The goal is not causal inference. The goal is to understand what is present, how complete it is, and where the data are sparse or structurally imbalanced.

## Core Structure

The table is a one-row-per-finding dataset.

- Total rows: `13,023`
- Distinct finding IDs: `13,023`
- Distinct studies: `1,601`
- Distinct intervention IDs: `186`
- Distinct named interventions: `186`
- Distinct citations: `1,557`

The row count matching the distinct finding ID count confirms that the original table is already at finding-level grain.

## Metric Coverage

Coverage is strong for the main outcome fields but uneven for intervention-level fields.

- `f_effect_size_wwc`: `10,553` rows, `81.0%`
- `f_effect_size_study`: `7,647` rows, `58.7%`
- `f_improvement_index`: `12,190` rows, `93.6%`
- `f_p_value_wwc`: `12,025` rows, `92.3%`
- `f_is_statistically_significant`: `12,905` rows, `99.1%`
- `f_outcome_intervention_ss`: `12,892` rows, `99.0%`
- `f_outcome_comparison_ss`: `12,892` rows, `99.0%`
- `f_finding_rating`: `10,259` rows, `78.8%`
- `f_essa_rating`: `2,097` rows, `16.1%`
- `s_study_design`: `13,011` rows, `99.9%`
- `s_publication_date`: `13,023` rows, `100.0%`

Practical interpretation:
- `f_effect_size_wwc` and `f_improvement_index` are the main usable effect metrics.
- `f_improvement_index` has the best coverage of the impact measures.
- `f_essa_rating` is too sparse to use as a universal filter.

## Identifier Missingness

The major structural gap is at the intervention level.

- Missing `f_findingid`: `0`
- Missing `s_studyid`: `0`
- Missing `i_interventionid`: `9,965`
- Missing `i_intervention_name`: `9,965`
- Missing `s_citation`: `0`
- Missing `i_outcome_domain`: `9,965`
- Missing `f_outcome_domain`: `0`

This means the dataset is fully usable at finding/study level, but many rows do not carry intervention-level metadata. Any intervention-level summary must report missing-name coverage explicitly.

## Publication Year Coverage

Publication dates are almost fully parseable.

- Rows with parseable publication year: `13,013`
- Rows without parseable publication year: `10`
- Minimum year: `1984`
- Maximum year: `2024`
- Distinct years: `41`

The publication-year distribution shows a heavy concentration in the 2010s and early 2020s, with a strong peak around `2010`, `2016`, `2019`, and `2020`.

## Study Design Profile

Normalized study design counts:

- Randomized controlled trial: `10,658`
- Quasi-experimental design: `2,129`
- Single case design: `201`
- Regression discontinuity design: `23`
- Missing: `12`

The table is dominated by randomized controlled trials, which is useful for evidence quality but limits design-based comparisons because there is very little variation in study design.

## Finding and Effectiveness Labels

Finding quality:

- `Meets WWC standards without reservations`: `7,280`
- `Meets WWC standards with reservations`: `2,979`
- Missing: `2,764`

Intervention effectiveness rating:

- Missing: `9,965`
- `No Discernible Effects`: `926`
- `Potentially Positive Effects`: `879`
- `Positive Effects`: `796`
- `Mixed Effects`: `393`
- `Not Measured`: `35`
- `Potentially Negative Effects`: `25`
- `N/A`: `4`

The effectiveness rating is sparse because it is not populated for many rows. Use it as a descriptive intervention-level field, not as a universal outcome variable.

## Sample Size Coverage

- `i_sample_size_intervention`: `3,058` rows
- `f_outcome_sample_size`: `13,015` rows
- `f_intervention_clusters_ss`: `10,883` rows
- `f_comparison_clusters_ss`: `10,833` rows

This is enough to support sample-size-aware summaries, but not enough to assume full completeness for every row.

## Main Structural Caveats

1. Intervention metadata is missing on most rows.
2. Intervention-level comparisons must be framed carefully because `i_interventionid` and `i_intervention_name` are absent for `9,965` rows.
3. `f_essa_rating` is too sparse for general use.
4. The table is already at finding grain, so row counts are not study counts.
5. Many useful questions are descriptive moderator questions, not causal inference questions.

## Bottom Line

The original WWC table is structurally strong for finding-level evidence summaries and publication-year trends. It is weaker for intervention-level profiling because most rows lack intervention identifiers and names. For the poster and downstream EDA, the safest high-value metrics are:

- `f_effect_size_wwc`
- `f_improvement_index`
- `f_p_value_wwc`
- `f_is_statistically_significant`
- publication year
- study design

These support a rigorous overview of the evidence base while keeping the limitations explicit.
