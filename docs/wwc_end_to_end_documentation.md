# WWC 2026 ASA Expo: End-to-End Technical Documentation

Last updated: 2026-03-01  
Workspace: `/Volumes/Auxilary/Side_Projects/ASA Data Challange`

## 1) Executive Summary

This project builds a full workflow for answering the WWC question: **what works, for whom, and in which contexts**.

What was delivered:
- A normalized SQL mart design for WWC nested data (`interventions -> studies -> findings`).
- A mart build SQL script with parsing/derivations.
- A context-data fetch pipeline (ACS + SAIPE + RUCC) to create a mergeable `state_abbr, year` panel.
- Three multivariate model scripts (A/B/C) aligned with the research questions.
- A full visualization suite and rank tables in `outputs_ctx/`.

Current status:
- Pipeline runs end-to-end on your local WWC export plus external context.
- Results are now state-aware (51 unique state/DC mappings detected).
- Context still uses fallback proxies for missing NCES CCD/F-33 columns (documented below).

## 2) Problem Framing

Primary objective:
- Estimate heterogeneous intervention effects, not just average effectiveness.

Research questions implemented:
1. **Model A (Subgroup heterogeneity):** Which intervention families are most promising for high-FRPL / EL / SWD contexts?
2. **Model B (Resource moderation):** How does effectiveness vary with state-level poverty/resource proxies?
3. **Model C (Evidence equity + transportability):** Where is evidence sparse and prediction risk high?

## 3) Data Inputs

## 3.1 WWC source data (local)
- `WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv`
- `WWC-export-archive-2025-Aug-25-172838/ReviewDictionary.csv`
- `WWC-export-archive-2025-Aug-25-172838/ReadMe.txt`

Observed profile from processing:
- 13,023 finding-level rows in base WWC.
- 1,601 unique studies.
- Intervention IDs require canonical coalescing (`i_InterventionID`, `s_interventionID`, `f_InterventionID`).

## 3.2 External context data (fetched)

Generated files:
- `data/context_state_year_acs_saipe_rucc.csv`
- `data/context_state_year_acs_saipe_rucc.meta.json`

Sources used:
- ACS 5-year API (state-year socioeconomic/race/education fields)
- SAIPE API (child poverty and median income)
- USDA RUCC county file (aggregated to state rural share)

Coverage:
- 663 rows
- 51 states/DC
- Years 2012-2024 (ACS calls for 2009-2011 failed for the selected variable set)

## 4) Data Model and Engineering

## 4.1 SQL schema artifacts

Files:
- `sql/wwc_analytic_schema.sql`
- `sql/wwc_build_marts.sql`

Core marts:
- `mart.dim_intervention`
- `mart.dim_study`
- `mart.fact_finding`
- `mart.bridge_study_state`
- `mart.dim_context_state_year`
- view: `mart.v_finding_analytic`

## 4.2 Key transformations

- Canonical IDs:
  - `intervention_id = coalesce(i_InterventionID, s_interventionID, f_InterventionID)`
  - `study_id = s_StudyID`
  - `finding_id = f_FindingID`
- Effect metric:
  - `effect_size_final = coalesce(f_Effect_Size_WWC, f_Effect_Size_Study)`
- Quality encoding:
  - WWC study ratings mapped to ordinal score `0-3`
- Period parsing:
  - days/weeks/months/semesters/years to `period_months`
- Approximate variance weights:
  - `se_approx ~ sqrt(4 / outcome_sample_size)`
  - `weight_iv = 1 / se_approx^2`
- State bridge:
  - Expanded from one-hot `s_Region_State_*` columns
  - Fixed parser to handle numeric boolean encoding (`1.0` / `0.0`)

## 4.3 Modeling dataset behavior

Because studies may map to multiple states, rows are expanded through state bridge with `state_weight`.  
Effective rows used in model runs: **23,691**.

## 5) Modeling Design

Files:
- `analysis/_utils.py` (prep + feature engineering + weighted linear fitting)
- `analysis/01_fit_model_a.py`
- `analysis/02_fit_model_b.py`
- `analysis/03_fit_model_c.py`
- `analysis/run_all.py`
- `analysis/model_specs.py`

Implementation choice:
- Baseline models are weighted linear models (`scikit-learn`) due local env constraints (`statsmodels` unavailable).
- Designed to mimic first-pass meta-regression behavior with inverse-variance-inspired weights.

Engineered predictors:
- Demographic shares: FRPL, EL, SWD, minority
- Design controls: study design + quality score + year centered
- Intervention families from WWC type flags/name heuristics
- Context terms from fetched data + controlled fallback proxies

Important note:
- `context_source_values = ['merged_external_with_proxy_fallback']` in all three models.
- This means external context is merged, but missing columns (especially CCD/F-33) are still backfilled by proxy logic.

## 6) Visual Analytics Delivered

Model A:
- `outputs_ctx/model_a/coef_top30.png`
- `outputs_ctx/model_a/heterogeneity_heatmap_frpl.png`
- `outputs_ctx/model_a/observed_vs_predicted.png`
- `outputs_ctx/model_a/intervention_rank_by_frpl_band.csv`

Model B:
- `outputs_ctx/model_b/coef_resource_terms.png`
- `outputs_ctx/model_b/moderation_curves.png`
- `outputs_ctx/model_b/state_resource_bubble.png`
- `outputs_ctx/model_b/state_resource_summary.csv`

Model C:
- `outputs_ctx/model_c/coverage_heatmap.png`
- `outputs_ctx/model_c/transport_risk_top25.png`
- `outputs_ctx/model_c/impact_vs_transport_risk.png`
- `outputs_ctx/model_c/intervention_rank_by_subgroup.csv`
- `outputs_ctx/model_c/transport_risk_by_state_subgroup.csv`

## 7) Quantitative Results Snapshot

## 7.1 Model fit metrics

From `outputs_ctx/model_*/metrics.json`:

| Model | Rows | Features | Weighted R2 |
|---|---:|---:|---:|
| A (Subgroup heterogeneity) | 23,691 | 90 | 0.009994 |
| B (Resource moderation) | 23,691 | 98 | 0.005664 |
| C (Transportability) | 23,691 | 81 | 0.005076 |

Interpretation:
- Explanatory power is low (expected for noisy, heterogeneous education-effect meta data).
- Value here is primarily **rank/relative heterogeneity insight**, not point-forecast accuracy.

## 7.2 Model A (by FRPL band, predicted effect)

Top intervention families by band:

- Low FRPL:
  - College Access: `0.286`
  - Tutoring: `0.232`
  - Supplement: `0.061`
- Mid FRPL:
  - Curriculum: `0.494`
  - Tutoring: `0.271`
  - Practice: `0.218`
- High FRPL:
  - Tutoring: `0.350`
  - Teacher-Level: `0.084`
  - Supplement: `0.058`

Signal:
- Tutoring remains strong across FRPL levels, especially high-FRPL contexts.

## 7.3 Model B (state resource summaries)

States with most evidence volume:
- TX (1,796 findings), CA (1,751), NY (1,715), PA (1,054), NC (962)

Highest average effects among states with >= 50 findings:
- UT (`0.354`), AR (`0.221`), IN (`0.209`), MD (`0.208`), AL (`0.199`)

Signal:
- State-level differences exist but should be treated as **associational** due residual confounding and proxy covariates.

## 7.4 Model C (equity + transport risk)

Top intervention families by subgroup:
- General/Mixed: Tutoring (`0.276`), College Access (`0.223`)
- High EL: College Access (`0.380`), Tutoring (`0.335`)
- High Poverty: Tutoring (`0.333`), Supplement (`0.258`)

Highest transport-risk segments (top examples):
- OK, High Poverty + High EL
- WV, High Poverty
- RI, High Poverty
- SC, High Poverty

Signal:
- Transport risk concentrates where evidence counts are low and residual uncertainty is high.

## 8) Limitations and Risk to Interpretation

1. No full NCES CCD/F-33 integration yet
- `ccd_ell_share`, `ccd_swd_share`, and F-33 finance terms are placeholders/proxy-filled.

2. Baseline model class
- Current models are weighted linear approximations, not full hierarchical mixed-effects meta-regression.

3. Effect-size outliers
- Heavy-tailed outcomes persist (extreme values remain in some domains), which can affect coefficients and rank stability.

4. Geographic mapping assumptions
- Study-state expansion assumes equal weighting across flagged states.

## 9) Reproducibility

## 9.1 Build context data

```bash
python3 analysis/fetch_context_data.py \
  --year-start 2012 \
  --year-end 2024 \
  --out-csv data/context_state_year_acs_saipe_rucc.csv \
  --out-meta data/context_state_year_acs_saipe_rucc.meta.json
```

## 9.2 Run all models

```bash
python3 analysis/run_all.py \
  --wwc-csv "WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv" \
  --context-csv "data/context_state_year_acs_saipe_rucc.csv" \
  --outroot "outputs_ctx"
```

## 9.3 Optional SQL marts

Run:
1. `sql/wwc_analytic_schema.sql`
2. `sql/wwc_build_marts.sql`

## 10) What Was Done, Why, and How (Traceability)

What we did:
- Designed normalized schema and ETL strategy for WWC nested data.
- Built Python analysis pipeline for iterative model runs and visualization export.
- Fetched and assembled real external context data into a mergeable panel.
- Identified/fixed multiple robustness issues (ID coalescing, numeric boolean parsing, plotting dtypes).

Why:
- WWC alone answers "what works" incompletely; subgroup/context augmentation is needed for "what works for whom."
- A reproducible, script-first workflow supports iterative exploration for ASA Expo deliverables.

How:
- Scripted transformation + model execution with deterministic outputs to `outputs_ctx/`.
- Used weighted models and stratified visual summaries to emphasize heterogeneity over single global averages.

## 11) Recommended Next Engineering Steps

1. Integrate official NCES CCD + F-33 state-year variables into the context CSV (replace proxies).
2. Add hierarchical mixed-effects/Bayesian model variants once `statsmodels`/PyMC stack is available.
3. Add bootstrap stability checks for subgroup rankings.
4. Produce final presentation notebook/report with narrative annotations tied to charts.

