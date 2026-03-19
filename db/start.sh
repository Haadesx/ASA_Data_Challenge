#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DB_CONTAINER="wwc_postgres"
DB_NAME="wwc"
DB_USER="wwc_user"
DB_PASS="wwc_password"

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

wait_for_docker() {
  local max_attempts=90
  local sleep_seconds=2
  local i

  if docker info >/dev/null 2>&1; then
    return 0
  fi

  echo "Docker daemon is not reachable."

  if [[ "$(uname -s)" == "Darwin" ]] && have_cmd open; then
    echo "Attempting to start Docker Desktop..."
    open -a Docker >/dev/null 2>&1 || true
  fi

  # If available, prefer desktop-linux context on macOS Docker Desktop.
  if docker context ls >/dev/null 2>&1 && docker context ls --format '{{.Name}}' | rg -qx 'desktop-linux'; then
    docker context use desktop-linux >/dev/null 2>&1 || true
  fi

  echo "Waiting for Docker daemon..."
  for i in $(seq 1 "$max_attempts"); do
    if docker info >/dev/null 2>&1; then
      echo "Docker is running."
      return 0
    fi
    sleep "$sleep_seconds"
  done

  echo "Docker is still unavailable after waiting."
  echo "Start Docker Desktop manually, then rerun: ./db/start.sh"
  return 1
}

wait_for_postgres() {
  local max_attempts=60
  local sleep_seconds=2
  local i

  echo "Waiting for PostgreSQL container readiness..."
  for i in $(seq 1 "$max_attempts"); do
    if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
      echo "PostgreSQL is ready."
      return 0
    fi
    sleep "$sleep_seconds"
  done

  echo "PostgreSQL did not become ready in time."
  return 1
}

show_row_counts() {
  local counts
  counts="$(docker exec -e PGPASSWORD="$DB_PASS" -i "$DB_CONTAINER" \
    psql -U "$DB_USER" -d "$DB_NAME" -t -A \
    -c "SELECT (SELECT COUNT(*) FROM raw.wwc_original)::text || ',' || (SELECT COUNT(*) FROM raw.wwc_aggregated)::text;" 2>/dev/null || true)"

  if [[ -n "$counts" ]]; then
    local original_rows aggregated_rows
    original_rows="${counts%%,*}"
    aggregated_rows="${counts##*,}"
    echo "Loaded rows: raw.wwc_original=$original_rows, raw.wwc_aggregated=$aggregated_rows"
  else
    echo "Tables are initializing or unavailable."
  fi
}

main() {
  if ! have_cmd docker; then
    echo "docker CLI not found. Install Docker Desktop (or Docker + daemon) first."
    return 1
  fi

  if ! have_cmd rg; then
    echo "ripgrep (rg) not found; continuing without context auto-check."
  fi

  wait_for_docker

  echo "Starting services with docker compose..."
  docker compose up -d

  wait_for_postgres
  show_row_counts

  cat <<EOF

Done. Connect with:
  docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME

Or from host:
  PGPASSWORD=$DB_PASS psql -h localhost -p 5433 -U $DB_USER -d $DB_NAME
EOF
}

main "$@"
