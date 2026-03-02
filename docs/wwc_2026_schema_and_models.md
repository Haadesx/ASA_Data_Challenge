# WWC 2026: Schema + First-Pass Model Specs

This blueprint is tailored to your local export file:
`WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv`

Quick profile from this file:
- Rows (finding-level): `13,023`
- Unique studies (`s_StudyID`): `1,601`
- Unique findings (`f_FindingID`): `13,023`
- Unique intervention IDs in `i_InterventionID`: `186`
- `i_InterventionID` missing on `9,965` rows, but `s_interventionID` is present there

## 1) Concrete Analytic Schema

Use a finding-centered warehouse with canonical IDs and context side tables.

### Tables

1. `mart.dim_intervention`
- Grain: one row per canonical intervention.
- Key: `intervention_id` (BIGINT).
- Source: `COALESCE(i_InterventionID, s_interventionID, f_InterventionID)`.
- Core fields:
  - `intervention_name` (`COALESCE(i_Intervention_Name, s_Intervention_Name, f_Intervention_Name)`)
  - `protocol`, `protocol_version`
  - intervention-level design flags (`i_Program_Type_*`, `i_Delivery_Method_*`)
  - intervention-level sample composition (`i_Demographics_*`, `i_Race_*`)

2. `mart.dim_study`
- Grain: one row per `s_StudyID`.
- Key: `study_id`.
- Core fields:
  - `review_id`
  - `study_rating`, `study_design`, `standards_version`
  - `publication`, `publication_date`, `posting_date`
  - study-level demographics (`s_Demographics_*`, `s_Race_*`, `s_Gender_*`)
  - grade flags (`s_Grade_*`), topic flags (`s_Topic_*`)
  - `study_quality_score` (derived ordinal)

3. `mart.fact_finding`
- Grain: one row per `f_FindingID` (primary analytic fact table).
- Key: `finding_id`.
- Foreign keys: `study_id`, `intervention_id`.
- Core fields:
  - outcomes: `f_Outcome_Domain`, `f_Outcome_Measure`, `f_Period`
  - effect metrics: `f_Effect_Size_WWC`, `f_Effect_Size_Study`, `f_Improvement_Index`
  - significance: `f_p_Value_WWC`, `f_Is_Statistically_Significant`, `f_FavorableUnfavorableDesignation`
  - sample sizes: `f_Outcome_Sample_Size`, `f_Outcome_Intervention_SS`, `f_Outcome_Comparison_SS`
  - subgroup marker: `f_Is_Subgroup`
  - finding quality: `f_Finding_Rating`, `f_ESSA_Rating`
  - derived columns:
    - `effect_size_final` (`COALESCE(f_Effect_Size_WWC, f_Effect_Size_Study)`)
    - `effect_abs` (`ABS(effect_size_final)`)
    - `sig_flag` (boolean from `f_Is_Statistically_Significant`)
    - `period_months` (parsed numeric duration)
    - `se_approx` (derived standard error; see below)
    - `weight_iv` (`1 / se_approx^2`)

4. `mart.bridge_study_state`
- Grain: one row per (`study_id`, `state_abbr`) from one-hot columns `s_Region_State_*`.
- Purpose: deterministic joins to NCES/ACS state-year context.

5. `mart.dim_context_state_year`
- Grain: one row per (`state_abbr`, `year`).
- Merged from secondary datasets:
  - NCES CCD / EDFacts (demographics, FRPL, EL, SWD)
  - NCES F-33 (district finance aggregates -> state-year rollups)
  - Census SAIPE (child poverty)
  - ACS 5-year (income, race/ethnicity, education)
  - USDA RUCC (rurality; state share or study-level mapped where possible)

## 2) Join Keys and Harmonization Rules

### Canonical IDs

- `intervention_id = COALESCE(i_InterventionID, s_interventionID, f_InterventionID)::BIGINT`
- `study_id = s_StudyID::BIGINT`
- `finding_id = f_FindingID::BIGINT`

### Time alignment

- `analysis_year = EXTRACT(YEAR FROM s_Publication_Date)` (fallback `s_Posting_Date`).
- For ACS 5-year and SAIPE: map to nearest available year, preferring same year.
- For F-33/CCD/EDFacts: align to same school year (publication year fallback if unknown).

### State alignment

- Pivot `s_Region_State_*` booleans into `state_abbr`.
- If multiple states are flagged in a study, duplicate rows in `bridge_study_state` and apply equal study-state weights in downstream summaries.

### Critical cleaning rules

1. Standardize casing categories:
- `Randomized Controlled Trial` and `Randomized controlled trial` -> one category.

2. Winsorize extreme effect sizes (recommended):
- `effect_size_final` at p0.5/p99.5 within outcome domain.

3. Build quality score:
- `Meets WWC standards without reservations` = `3`
- `Meets WWC standards with reservations` = `2`
- `Does not meet` = `1`
- `Ineligible/blank` = `0`

4. Approximate standard error:
- If `p_value` available and `effect_size_final != 0`:
  - `z = qnorm(1 - p/2)`, `se_approx = abs(effect_size_final) / z`
- Else fallback:
  - `se_approx = sqrt(4 / f_Outcome_Sample_Size)` with floor guard on n.

## 3) First-Pass Model Formulas

Use these as baseline specifications, then iterate.

### Model A: Who benefits most? (Subgroup heterogeneity)

Response:
- `y = effect_size_final`

Mixed-effects meta-regression:

`y_f ~ 1 + C(intervention_family) + frpl_share + ell_share + swd_share + minority_share + C(grade_band) + C(urbanicity) + C(study_design_std) + study_quality_score + publication_year_c + C(intervention_family):frpl_share + C(intervention_family):ell_share + C(intervention_family):swd_share + (1 | intervention_id) + (1 | study_id) + (1 | outcome_domain)`

Weights:
- `weight_iv = 1 / se_approx^2`

### Model B: Resource moderation (under-resourced vs well-resourced)

Response:
- `y = effect_size_final`

`y_f ~ 1 + C(intervention_family) + log_pp_exp + child_poverty_rate + teacher_salary_real + frpl_share + ell_share + study_quality_score + C(study_design_std) + publication_year_c + C(intervention_family):log_pp_exp + C(intervention_family):child_poverty_rate + (1 | intervention_id) + (1 | study_id) + (1 | state_abbr) + (1 | outcome_domain)`

Where:
- `log_pp_exp`: log real per-pupil expenditure from F-33
- `child_poverty_rate`: SAIPE

### Model C: Evidence equity + transportability

Part 1: coverage model (where evidence is sparse):

`n_findings_{g,s,d} ~ NegBin( exp( alpha + C(subgroup_g) + C(state_s) + C(domain_d) + year_c ) )`

Part 2: hierarchical transport model:

`y_f ~ 1 + C(intervention_family) + acs_income_z + acs_ba_z + acs_race_comp + rucc_rural_share + frpl_share + ell_share + C(intervention_family):rucc_rural_share + (1 | intervention_id) + (1 | study_id) + (1 | state_abbr) + (1 | outcome_domain)`

Output:
- Predicted effect by target subgroup/context.
- Posterior/prediction interval width used as “transport risk”.

## 4) Agentic Iterative Workflow (Implementation Loop)

### Phase 1: Ingest and normalize
1. Load WWC CSV to `stg.wwc_raw`.
2. Build canonical IDs and normalized dimensions/fact.
3. Emit QC report:
   - missingness
   - key integrity
   - category cardinalities
   - outlier scan

### Phase 2: External context merges
1. Load NCES/SAIPE/ACS/RUCC source tables.
2. Build `dim_context_state_year`.
3. Join through `bridge_study_state` + `analysis_year`.
4. Emit merge diagnostics:
   - join rate by table
   - state-year holes
   - imputation map

### Phase 3: Baseline multivariate models
1. Fit Models A/B/C with fixed spec.
2. Save coefficient tables, random effects, and fit metrics.
3. Produce subgroup “what works for whom” ranking tables.

### Phase 4: Iterative refinement
1. Diagnose residuals, leverage, and variance components.
2. Adjust encoding/winsorization/interactions.
3. Refit and compare:
   - AIC/BIC/WAIC
   - out-of-fold RMSE or log score
   - subgroup rank stability

### Phase 5: Final outputs
1. Reproducible result tables:
   - top interventions by subgroup and context
   - context moderation effects
   - high-need low-evidence flags
2. Export charts and a methods appendix.

## 5) Suggested Repo Layout to Start Coding

- `sql/wwc_analytic_schema.sql` (DDL + indexes)
- `sql/wwc_build_marts.sql` (ETL transformations)
- `analysis/01_fit_model_a.py`
- `analysis/02_fit_model_b.py`
- `analysis/03_fit_model_c.py`
- `analysis/_utils.py`
- `outputs/` (model summaries, diagnostics, tables)

