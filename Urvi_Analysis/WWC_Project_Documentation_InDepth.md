# WWC Project Documentation (In-Depth)

Project: ASA Data Challenge (WWC)  
Workspace: `/Volumes/Auxilary/Side_Projects/ASA Data Challange`  
Documentation date: March 2, 2026

## 1) Purpose and Problem Statement

The objective is to answer the WWC challenge question in a rigorous and practical way:
- **What works?**
- **For whom?**
- **Under what conditions?**

The raw WWC data is nested and sparse in several key predictors. The project therefore required:
- careful feature-level availability analysis,
- defensible subset design,
- a reproducible modeling workflow,
- and a decision-ready dashboard for team and mentor alignment.

## 2) Timeline: What Was Done, When

## Phase 1: Core pipeline build (February 28, 2026)
- Parsed WWC export and reviewed dictionary/metadata.
- Built analytic schema + mart scripts:
  - `sql/wwc_analytic_schema.sql`
  - `sql/wwc_build_marts.sql`
- Built model scripts and output pipeline:
  - `analysis/01_fit_model_a.py`
  - `analysis/02_fit_model_b.py`
  - `analysis/03_fit_model_c.py`
  - `analysis/run_all.py`
- Generated first round of outputs in `outputs/` and context-aware outputs in `outputs_ctx/`.

## Phase 2: External context integration (February 28, 2026)
- Implemented context fetch:
  - `analysis/fetch_context_data.py`
- Built merged context file:
  - `data/context_state_year_acs_saipe_rucc.csv`
- Re-ran all models with external context merge.

## Phase 3: Data-readiness and subset strategy (March 2, 2026)
- Profiled teammate’s aggregated file:
  - `Urvi_Analysis/asadata_aggregated.csv`
- Created variable-level and level-of-analysis profile:
  - `Urvi_Analysis/column_level_profile.csv`
- Produced mentor strategy note:
  - `Urvi_Analysis/mentor_data_availability_plan.md`

## Phase 4: Professional dashboard and dual-source enrichment (March 2, 2026)
- Built a new dashboard generator with stronger UX and decision framing:
  - `Urvi_Analysis/scripts/generate_subsets_dashboard.py`
- Combined aggregated + original WWC export into enriched base:
  - `Urvi_Analysis/data_products/combined_enriched_base.csv`
- Generated renamed subsets and dashboard:
  - `Urvi_Analysis/data_products/predictive_modeling_core.csv`
  - `Urvi_Analysis/data_products/inference_ci_core.csv`
  - `Urvi_Analysis/data_products/geography_context_core.csv`
  - `Urvi_Analysis/data_products/demographic_strict_subset.csv`
  - `Urvi_Analysis/dashboard/data_readiness_dashboard.html`

## 3) What We Did and Why

## 3.1 Audited data at the column + hierarchy level

Why:
- Prevent weak modeling decisions due hidden sparsity.
- Identify where inference is defensible and where it is not.

What:
- Measured non-missing coverage, unique values, and level consistency.
- Confirmed dataset grain is primarily finding-level.
- Confirmed geography is state-level only (no county or school IDs).

Outcome:
- Established clear feasibility boundaries for ML, CI, geography, and subgroup analyses.

## 3.2 Built dual-source enriched base (aggregated + original WWC)

Why:
- Aggregated file is convenient but drops one-hot detail.
- Original file contains useful granular indicators (state flags, topic flags, grade flags, school/urbanicity indicators).

What:
- Merged by `f_FindingID` (13,023/13,023 match).
- Added 217 extra columns from the original export.
- Derived unified availability features:
  - `state_specific_available`
  - `urbanicity_available`
  - `school_type_available`
  - `demographic_signal_available`

Impact:
- Enriched base increased from 90 to 315 columns, enabling more explicit subset design and better dashboard diagnostics.

## 3.3 Reframed subsets with clearer names and strict definitions

Why:
- Previous names (`ml_core`, `ci_core`, etc.) were short but less descriptive for stakeholder communication.

What:
- Created decision-oriented subset names and rules:
  - `predictive_modeling_core`
  - `inference_ci_core`
  - `geography_context_core`
  - `demographic_strict_subset`

Impact:
- Reduced ambiguity in mentor/team discussions.
- Improved traceability from recommendation -> subset -> model pipeline.

## 3.4 Built a professional, decision-first dashboard

Why:
- A basic dashboard is insufficient for mentor review and project governance.
- Needed a tool that answers “should we proceed, and with what?”

What:
- Upgraded design with:
  - executive decision header,
  - composite readiness score,
  - GO / Cautious / NO-GO matrix,
  - required-field coverage heatmap,
  - U.S. state evidence map,
  - support and coverage distribution charts.

Impact:
- Dashboard now supports concrete decision-making, not just descriptive viewing.

## 4) Current Results (Most Important Numbers)

Base data (combined):
- Rows: 13,023
- Findings: 13,023
- Studies: 1,601
- Interventions: 1,035
- Columns: 315

Availability signals:
- `state_specific_available`: 68.0%
- `urbanicity_available`: 66.9%
- `school_type_available`: 54.3%
- `demographic_signal_available`: 87.2%

Subset readiness:
- `predictive_modeling_core`: 6,994 rows, 848 studies, 607 interventions -> **GO**
- `inference_ci_core`: 10,329 rows, 1,315 studies, 903 interventions -> **GO**
- `geography_context_core`: 2,984 rows, 363 studies, 290 interventions -> **GO (Cautious)**
- `demographic_strict_subset`: 1,521 rows, 206 studies, 153 interventions -> **NO-GO** (as primary)

Composite readiness score in dashboard:
- **68.9 / 100**

## 5) How This Was Impactful

Technical impact:
- Converted a sparse, nested dataset into reproducible, model-ready pipelines.
- Removed uncertainty around variable availability and analysis level.
- Produced reusable subset products for immediate modeling.

Project impact:
- Team can now split work cleanly:
  - inference track (`inference_ci_core`)
  - predictive track (`predictive_modeling_core`)
- Mentor communication is now evidence-backed and concrete.

Decision impact:
- Clear “go/no-go” boundaries avoid over-claiming from weak subsets.
- State-level analyses can proceed; county/school-level claims are explicitly out of scope.

## 6) Methods and Reproducibility

Regenerate everything:

```bash
python3 /Volumes/Auxilary/Side_Projects/ASA\ Data\ Challange/Urvi_Analysis/scripts/generate_subsets_dashboard.py
```

Open dashboard:

```bash
open /Volumes/Auxilary/Side_Projects/ASA\ Data\ Challange/Urvi_Analysis/dashboard/data_readiness_dashboard.html
```

Primary generated outputs:
- `Urvi_Analysis/data_products/combined_enriched_base.csv`
- `Urvi_Analysis/data_products/subset_readiness_summary.csv`
- `Urvi_Analysis/data_products/column_coverage_summary.csv`
- `Urvi_Analysis/data_products/required_column_coverage_matrix.csv`
- `Urvi_Analysis/data_products/state_coverage_summary.csv`
- `Urvi_Analysis/data_products/topic_coverage_summary.csv`

## 7) Recommended Path Forward

## Immediate next 1-3 days
1. Run predictive models on `predictive_modeling_core.csv`.
2. Run inference/meta-regression with uncertainty reporting on `inference_ci_core.csv`.
3. Use `geography_context_core.csv` for state-context analyses with cautious interpretation.

## Short-term next week
1. Add robust cross-validation, subgroup stability checks, and intervention support thresholds.
2. Produce one integrated results dashboard or notebook with:
   - effect heterogeneity,
   - uncertainty intervals,
   - evidence support counts.
3. Promote only findings that are stable across folds/specs.

## Before final submission
1. Expand external context (NCES CCD + F-33 real values, not fallbacks).
2. Move to mixed-effects/Bayesian hierarchical modeling for stronger inferential credibility.
3. Prepare a methods appendix explicitly documenting:
   - subset logic,
   - missingness handling,
   - limitations and non-claim boundaries.

## 8) Risks and Guardrails

Main risks:
- Sparse demographic strict subset can produce unstable subgroup claims.
- Context variables still include fallback logic in some analyses.
- Causal claims are limited by observational and mixed-study design structure.

Guardrails:
- Treat `demographic_strict_subset` as sensitivity-only.
- Require minimum support thresholds before ranking interventions.
- Keep state-level interpretations associational unless stronger design assumptions hold.

## 9) Final Recommendation

Proceed now with a **two-track execution plan**:
1. **Inference track:** `inference_ci_core.csv`
2. **Prediction track:** `predictive_modeling_core.csv`

Use the dashboard as the team’s shared operating artifact for scope, status, and claim discipline.

