# WWC Postgres Schema Brief

This brief supports the delegated SQL agent in `.claude/agents/wwc-postgres-analyst.md`.

## Database

- container: `wwc_postgres`
- database: `wwc`
- user: `wwc_user`
- host port: `5433`

## Canonical Tables

### `raw.wwc_original`

Primary analysis table.

Grain:
- one row per finding

Structure:
- `i_*`: intervention-level columns
- `s_*`: study-level columns
- `f_*`: finding-level columns

Commonly used fields:
- identifiers: `f_findingid`, `s_studyid`
- intervention: `i_intervention_name`, `i_outcome_domain`
- study: `s_citation`, `s_publication_date`
- outcome: `f_effect_size_wwc`, `f_improvement_index`, `f_p_value_wwc`, `f_is_statistically_significant`

Coding notes:
- many numeric-looking fields are stored as text and require casting
- blank strings should be treated as missing before casting
- state and urbanicity indicators often use values like `'1.00'`
- subgroup flags may overlap
- intervention names are often missing

### `raw.wwc_aggregated`

Secondary table.
Use only when explicitly requested.
Do not assume it is a true collapsed aggregation.

## Frequently Used Filter Pattern

```sql
WHERE s_region_state_texas = '1.00'
```

## Frequently Used Numeric Cast Pattern

```sql
AVG(NULLIF(f_effect_size_wwc, '')::numeric)
```

## Current Known Texas Example

These values are useful as a sanity check for the current repo state:

- Texas total rows: `1812`
- Texas urban rows: `1240`
- Texas rural rows: `417`
- Texas rural-and-urban overlap: `369`

Bucketed Texas urbanicity example:
- `urban_only`: `871`, mean effect `0.12987273565523225712`
- `unlabeled`: `508`, mean effect `0.11714700398850987965`
- `both`: `369`, mean effect `0.11598975055456032833`
- `rural_only`: `48`, mean effect `0.35630409615871652405`
- `suburban_only`: `16`, mean effect `0.27391871653583546923`

## Existing Reproducible Query Pack

- `db/queries/texas_urbanicity_eda.sql`

## Existing Report

- `db/reports/texas_urbanicity_report.md`
