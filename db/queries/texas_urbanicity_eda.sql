\pset pager off

-- Texas WWC urbanicity EDA on the original imported table.
-- Run with:
--   ./db/run_query.sh db/queries/texas_urbanicity_eda.sql

\echo '== Table counts =='
SELECT COUNT(*) AS original_rows FROM raw.wwc_original;
SELECT COUNT(*) AS aggregated_rows FROM raw.wwc_aggregated;

\echo '== Texas overall, urban, rural =='
SELECT
  'texas_overall' AS subset_name,
  COUNT(*) AS rows_n,
  AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect
FROM raw.wwc_original
WHERE s_region_state_texas = '1.00'
UNION ALL
SELECT
  'texas_urban' AS subset_name,
  COUNT(*) AS rows_n,
  AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect
FROM raw.wwc_original
WHERE s_region_state_texas = '1.00'
  AND s_urbanicity_urban = '1.00'
UNION ALL
SELECT
  'texas_rural' AS subset_name,
  COUNT(*) AS rows_n,
  AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect
FROM raw.wwc_original
WHERE s_region_state_texas = '1.00'
  AND s_urbanicity_rural = '1.00';

\echo '== Texas overlap count =='
SELECT COUNT(*) AS rural_urban_overlap
FROM raw.wwc_original
WHERE s_region_state_texas = '1.00'
  AND s_urbanicity_rural = '1.00'
  AND s_urbanicity_urban = '1.00';

\echo '== Texas urbanicity buckets =='
SELECT
  CASE
    WHEN s_urbanicity_rural = '1.00' AND s_urbanicity_urban = '1.00' THEN 'both'
    WHEN s_urbanicity_rural = '1.00' THEN 'rural_only'
    WHEN s_urbanicity_urban = '1.00' THEN 'urban_only'
    WHEN s_urbanicity_suburban = '1.00' THEN 'suburban_only'
    ELSE 'unlabeled'
  END AS tx_urbanicity_group,
  COUNT(*) AS rows_n,
  AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect
FROM raw.wwc_original
WHERE s_region_state_texas = '1.00'
GROUP BY 1
ORDER BY rows_n DESC;

\echo '== Intervention name coverage in Texas =='
SELECT
  CASE
    WHEN i_intervention_name IS NULL OR btrim(i_intervention_name) = '' THEN 'missing_name'
    ELSE 'named'
  END AS intervention_name_status,
  COUNT(*) AS rows_n
FROM raw.wwc_original
WHERE s_region_state_texas = '1.00'
GROUP BY 1
ORDER BY rows_n DESC;

\echo '== Named interventions by Texas urbanicity bucket (>= 10 rows) =='
SELECT
  CASE
    WHEN s_urbanicity_rural = '1.00' AND s_urbanicity_urban = '1.00' THEN 'both'
    WHEN s_urbanicity_rural = '1.00' THEN 'rural_only'
    WHEN s_urbanicity_urban = '1.00' THEN 'urban_only'
    WHEN s_urbanicity_suburban = '1.00' THEN 'suburban_only'
    ELSE 'unlabeled'
  END AS tx_urbanicity_group,
  i_intervention_name,
  COUNT(*) AS rows_n,
  AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect
FROM raw.wwc_original
WHERE s_region_state_texas = '1.00'
  AND i_intervention_name IS NOT NULL
  AND btrim(i_intervention_name) <> ''
GROUP BY 1, 2
HAVING COUNT(*) >= 10
ORDER BY tx_urbanicity_group, rows_n DESC;
