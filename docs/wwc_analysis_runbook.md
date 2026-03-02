# WWC Analysis Runbook (Models + Visuals)

## 1) Build SQL marts (PostgreSQL)

Run in order:

1. `sql/wwc_analytic_schema.sql`
2. `sql/wwc_build_marts.sql`

Expected QC check:

```sql
SELECT * FROM mart.v_build_qc;
```

## 2) Run model scripts (CSV-based path)

From repo root:

Build external context CSV:

```bash
python3 analysis/fetch_context_data.py \
  --year-start 2012 \
  --year-end 2024 \
  --out-csv "data/context_state_year_acs_saipe_rucc.csv" \
  --out-meta "data/context_state_year_acs_saipe_rucc.meta.json"
```

Then run all models:

```bash
python3 analysis/run_all.py \
  --wwc-csv "WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv" \
  --context-csv "data/context_state_year_acs_saipe_rucc.csv" \
  --outroot "outputs_ctx"
```

With external context merge:

```bash
python3 analysis/run_all.py \
  --wwc-csv "WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv" \
  --context-csv "/absolute/path/state_year_context.csv"
```

Required context columns:
- `state_abbr`
- `year`

Recommended additional columns:
- `ccd_frpl_share`, `ccd_ell_share`, `ccd_swd_share`
- `f33_pp_expenditure_real`, `f33_teacher_salary_real`
- `saipe_child_poverty_rate`
- `acs_median_income_real`, `acs_ba_share`
- `rucc_rural_share`

## 3) Visualization outputs

Each model writes to:
- `outputs/model_a/`
- `outputs/model_b/`
- `outputs/model_c/`

Key charts:
- `model_a/heterogeneity_heatmap_frpl.png`
- `model_b/moderation_curves.png`
- `model_b/state_resource_bubble.png`
- `model_c/coverage_heatmap.png`
- `model_c/transport_risk_top25.png`
- `model_c/impact_vs_transport_risk.png`

## 4) Interpretation notes

- If no `--context-csv` is passed, scripts generate proxy context features from WWC demographics.
- Use proxy mode for pipeline validation only.
- For competition-grade inference, provide real NCES/ACS/SAIPE/RUCC merged context.
