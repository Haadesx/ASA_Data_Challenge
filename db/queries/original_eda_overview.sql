\pset pager off
\pset null '(null)'

-- Original WWC dataset overview/profile on raw.wwc_original only.
-- Run with:
--   ./db/run_query.sh db/queries/original_eda_overview.sql

\echo '== Core row and entity counts =='
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT f_findingid) AS distinct_finding_ids,
  COUNT(DISTINCT s_studyid) AS distinct_studies,
  COUNT(DISTINCT i_interventionid) AS distinct_intervention_ids,
  COUNT(DISTINCT NULLIF(btrim(i_intervention_name), '')) AS distinct_named_interventions,
  COUNT(DISTINCT NULLIF(btrim(s_citation), '')) AS distinct_citations
FROM raw.wwc_original;

\echo '== Key metric coverage =='
SELECT
  COUNT(*) AS total_rows,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_effect_size_wwc), '') IS NOT NULL) AS effect_size_wwc_nonmissing,
  ROUND(100.0 * COUNT(*) FILTER (WHERE NULLIF(btrim(f_effect_size_wwc), '') IS NOT NULL) / COUNT(*), 1) AS effect_size_wwc_pct,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_effect_size_study), '') IS NOT NULL) AS effect_size_study_nonmissing,
  ROUND(100.0 * COUNT(*) FILTER (WHERE NULLIF(btrim(f_effect_size_study), '') IS NOT NULL) / COUNT(*), 1) AS effect_size_study_pct,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_improvement_index), '') IS NOT NULL) AS improvement_index_nonmissing,
  ROUND(100.0 * COUNT(*) FILTER (WHERE NULLIF(btrim(f_improvement_index), '') IS NOT NULL) / COUNT(*), 1) AS improvement_index_pct,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_p_value_wwc), '') IS NOT NULL) AS p_value_wwc_nonmissing,
  ROUND(100.0 * COUNT(*) FILTER (WHERE NULLIF(btrim(f_p_value_wwc), '') IS NOT NULL) / COUNT(*), 1) AS p_value_wwc_pct,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_is_statistically_significant), '') IS NOT NULL) AS stat_sig_nonmissing,
  ROUND(100.0 * COUNT(*) FILTER (WHERE NULLIF(btrim(f_is_statistically_significant), '') IS NOT NULL) / COUNT(*), 1) AS stat_sig_pct,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_outcome_intervention_ss), '') IS NOT NULL) AS intervention_sample_nonmissing,
  ROUND(100.0 * COUNT(*) FILTER (WHERE NULLIF(btrim(f_outcome_intervention_ss), '') IS NOT NULL) / COUNT(*), 1) AS intervention_sample_pct,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_outcome_comparison_ss), '') IS NOT NULL) AS comparison_sample_nonmissing,
  ROUND(100.0 * COUNT(*) FILTER (WHERE NULLIF(btrim(f_outcome_comparison_ss), '') IS NOT NULL) / COUNT(*), 1) AS comparison_sample_pct,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_finding_rating), '') IS NOT NULL) AS finding_rating_nonmissing,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_essa_rating), '') IS NOT NULL) AS essa_rating_nonmissing,
  COUNT(*) FILTER (WHERE NULLIF(btrim(s_study_design), '') IS NOT NULL) AS study_design_nonmissing,
  COUNT(*) FILTER (WHERE NULLIF(btrim(s_publication_date), '') IS NOT NULL) AS publication_date_nonmissing
FROM raw.wwc_original;

\echo '== Core identifier missingness =='
SELECT
  COUNT(*) AS total_rows,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_findingid), '') IS NULL) AS missing_findingid,
  COUNT(*) FILTER (WHERE NULLIF(btrim(s_studyid), '') IS NULL) AS missing_studyid,
  COUNT(*) FILTER (WHERE NULLIF(btrim(i_interventionid), '') IS NULL) AS missing_interventionid,
  COUNT(*) FILTER (WHERE NULLIF(btrim(i_intervention_name), '') IS NULL) AS missing_intervention_name,
  COUNT(*) FILTER (WHERE NULLIF(btrim(s_citation), '') IS NULL) AS missing_citation,
  COUNT(*) FILTER (WHERE NULLIF(btrim(i_outcome_domain), '') IS NULL) AS missing_intervention_outcome_domain,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_outcome_domain), '') IS NULL) AS missing_finding_outcome_domain
FROM raw.wwc_original;

\echo '== Publication year coverage =='
WITH years AS (
  SELECT
    s_publication_date,
    substring(s_publication_date FROM '(\d{4})')::int AS pub_year
  FROM raw.wwc_original
)
SELECT
  COUNT(*) AS total_rows,
  COUNT(*) FILTER (WHERE pub_year IS NOT NULL) AS rows_with_parseable_year,
  COUNT(*) FILTER (WHERE pub_year IS NULL) AS rows_without_parseable_year,
  MIN(pub_year) AS min_year,
  MAX(pub_year) AS max_year,
  COUNT(DISTINCT pub_year) AS distinct_years
FROM years;

\echo '== Publication year distribution =='
WITH years AS (
  SELECT
    substring(s_publication_date FROM '(\d{4})')::int AS pub_year
  FROM raw.wwc_original
)
SELECT
  pub_year,
  COUNT(*) AS rows_n
FROM years
WHERE pub_year IS NOT NULL
GROUP BY 1
ORDER BY 1;

\echo '== Normalized study design profile =='
SELECT
  CASE
    WHEN s_study_design ILIKE '%randomized%' THEN 'randomized controlled trial'
    WHEN s_study_design ILIKE '%quasi%' THEN 'quasi-experimental design'
    WHEN s_study_design ILIKE '%regression discontinuity%' THEN 'regression discontinuity design'
    WHEN s_study_design ILIKE '%single case%' THEN 'single case design'
    WHEN NULLIF(btrim(s_study_design), '') IS NULL THEN 'missing'
    ELSE lower(btrim(s_study_design))
  END AS study_design_norm,
  COUNT(*) AS rows_n
FROM raw.wwc_original
GROUP BY 1
ORDER BY rows_n DESC, study_design_norm;

\echo '== Finding rating profile =='
SELECT
  COALESCE(NULLIF(btrim(f_finding_rating), ''), 'missing') AS finding_rating,
  COUNT(*) AS rows_n
FROM raw.wwc_original
GROUP BY 1
ORDER BY rows_n DESC, finding_rating;

\echo '== Effectiveness rating profile =='
SELECT
  COALESCE(NULLIF(btrim(i_effectiveness_rating), ''), 'missing') AS effectiveness_rating,
  COUNT(*) AS rows_n
FROM raw.wwc_original
GROUP BY 1
ORDER BY rows_n DESC, effectiveness_rating;

\echo '== Sample size coverage =='
SELECT
  COUNT(*) AS total_rows,
  COUNT(*) FILTER (WHERE NULLIF(btrim(i_sample_size_intervention), '') IS NOT NULL) AS intervention_sample_size_nonmissing,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_outcome_sample_size), '') IS NOT NULL) AS outcome_sample_size_nonmissing,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_intervention_clusters_ss), '') IS NOT NULL) AS intervention_clusters_nonmissing,
  COUNT(*) FILTER (WHERE NULLIF(btrim(f_comparison_clusters_ss), '') IS NOT NULL) AS comparison_clusters_nonmissing
FROM raw.wwc_original;
