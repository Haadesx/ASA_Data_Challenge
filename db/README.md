# Dockerized WWC Postgres

This setup loads two datasets into PostgreSQL via Docker:

- `raw.wwc_original` from `WWC-export-archive-2025-Aug-25-172838/Interventions_Studies_And_Findings.csv`
- `raw.wwc_aggregated` from `Urvi_Analysis/asadata_aggregated.csv`

## Why this setup

- Reproducible local SQL environment
- Both original and aggregated data in one DB
- Query-friendly, sanitized lowercase column names
- Explicit source-to-db mapping in `db/column_mappings/*.csv`

## Start

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

## Quick checks

```sql
SELECT COUNT(*) AS original_rows FROM raw.wwc_original;
SELECT COUNT(*) AS aggregated_rows FROM raw.wwc_aggregated;

SELECT s_region_state, AVG(NULLIF(f_effect_size_wwc, '')::numeric) AS mean_effect
FROM raw.wwc_original
WHERE s_region_state ILIKE '%Texas%'
GROUP BY 1
ORDER BY 2 DESC NULLS LAST
LIMIT 20;
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
