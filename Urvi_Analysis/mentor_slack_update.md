Here is the updated data-availability readout from the combined WWC base (`asadata_aggregated.csv` + original WWC export) and what we should do next.

1. What we have:
- 13,023 finding-level rows, 1,601 studies, 1,035 interventions.
- State-level geography is feasible (specific state tokens in 68.0% rows, 63.1% studies).
- County-level and school-ID level are not available in this file.
- Original export adds 217 extra columns (one-hot state/grade/topic detail), now included in the enriched base.

2. Analysis-ready subsets we created:
- `predictive_modeling_core.csv`: 6,994 rows (53.7%), 848 studies, 607 interventions -> **GO** for predictive ML.
- `inference_ci_core.csv`: 10,329 rows (79.3%), 1,315 studies, 903 interventions -> **GO** for CI/meta-regression.
- `geography_context_core.csv`: 2,984 rows (22.9%), 363 studies, 290 interventions -> **GO (Cautious)** for geography-context analyses.
- `demographic_strict_subset.csv`: 1,521 rows (11.7%), 206 studies, 153 interventions -> **NO-GO as primary**, use as targeted sensitivity only.

3. Tangible deliverables:
- Dashboard: `Urvi_Analysis/dashboard/data_readiness_dashboard.html`
- Subset summary: `Urvi_Analysis/data_products/subset_readiness_summary.csv`
- Column coverage: `Urvi_Analysis/data_products/column_coverage_summary.csv`
- Enriched combined base: `Urvi_Analysis/data_products/combined_enriched_base.csv`

4. Recommendation:
- Proceed with a two-track workflow:
  - Track A: inference using `inference_ci_core.csv`
  - Track B: prediction/heterogeneity using `predictive_modeling_core.csv`
- Reserve demographic-heavy analyses for focused follow-up due sparsity.
