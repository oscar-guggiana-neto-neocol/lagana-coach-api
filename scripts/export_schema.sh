#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

OUTPUT_PATH="db/schema.sql"

pg_dump --no-owner --schema-only "$DATABASE_URL" > "$OUTPUT_PATH"
echo "Schema exported to $OUTPUT_PATH"
