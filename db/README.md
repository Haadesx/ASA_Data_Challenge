# Dockerized WWC Postgres

This setup loads two datasets into PostgreSQL via Docker:

- `raw.wwc_original` from `WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv`
- `raw.wwc_aggregated` from `Urvi_Analysis/asadata_aggregated.csv`

## Why this setup

- Reproducible local SQL environment
- Both original and aggregated data in one DB
- Query-friendly, sanitized lowercase column names
- Explicit source-to-db mapping in `db/column_mappings/*.csv`
- Saved query packs and reports, similar to a lightweight analysis notebook but in SQL

## Start (recommended)

```bash
./db/start.sh
```

What `./db/start.sh` does:

- Checks Docker daemon availability
- Attempts to start Docker Desktop on macOS if needed
- Runs `docker compose up -d`
- Waits for PostgreSQL readiness
- Prints loaded-row counts and connection commands

## Start (manual fallback)

```bash
docker compose up -d
```

Container: `wwc_postgres`  
DB: `wwc`  
User: `wwc_user`  
Password: `wwc_password`  
Host port: `5433`

## Connect

```bash
docker exec -it wwc_postgres psql -U wwc_user -d wwc
```

Or from host:

```bash
PGPASSWORD=wwc_password psql -h localhost -p 5433 -U wwc_user -d wwc
```

## Run a saved query pack

```bash
./db/run_query.sh db/queries/texas_urbanicity_eda.sql
```

That query pack produces:

- table row counts
- Texas overall vs urban vs rural mean effect sizes
- rural/urban overlap count
- Texas urbanicity buckets
- intervention-name coverage in Texas
- named intervention summaries by urbanicity bucket

## Reports

- `db/reports/texas_urbanicity_report.md`: written interpretation of the saved Texas urbanicity EDA

## Quick checks

```sql
SELECT COUNT(*) AS original_rows FROM raw.wwc_original;
SELECT COUNT(*) AS aggregated_rows FROM raw.wwc_aggregated;

SELECT
  COUNT(*) AS texas_rows,
  AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect
FROM raw.wwc_original
WHERE s_region_state_texas = '1.00';
```

## Regenerate schema/mappings (if CSV headers change)

```bash
python3 db/scripts/generate_schema.py
```

Then rebuild from scratch:

```bash
docker compose down -v
docker compose up -d
```
