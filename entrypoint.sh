#!/bin/sh
set -e

mkdir -p /app/collected_static /app/media

python manage.py collectstatic --noinput

exec "$@"