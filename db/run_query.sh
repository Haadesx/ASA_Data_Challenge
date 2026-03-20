#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DB_CONTAINER="wwc_postgres"
DB_NAME="wwc"
DB_USER="wwc_user"

if [[ $# -lt 1 ]]; then
  echo "Usage: ./db/run_query.sh <sql-file>"
  exit 1
fi

SQL_FILE="$1"

if [[ ! -f "$SQL_FILE" ]]; then
  echo "SQL file not found: $SQL_FILE"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not reachable. Run ./db/start.sh first."
  exit 1
fi

docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -f - < "$SQL_FILE"
