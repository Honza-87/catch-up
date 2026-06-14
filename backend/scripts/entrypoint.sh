#!/usr/bin/env bash
# Apply migrations before serving (mkn10 parity), then run the API.
set -euo pipefail

alembic upgrade head

exec gunicorn catchup.app:app \
  -k uvicorn.workers.UvicornWorker \
  -b "0.0.0.0:${PORT:-8000}" \
  -w "${WEB_CONCURRENCY:-2}"
