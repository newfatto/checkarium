#!/bin/sh
set -e

mkdir -p /app/collected_static /app/media

chown -R appuser:appgroup /app/collected_static /app/media /app

exec "$@"
