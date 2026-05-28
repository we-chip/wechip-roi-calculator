#!/bin/sh
set -eu

pip install --quiet --disable-pip-version-check -r requirements.txt

exec gunicorn --bind=0.0.0.0:${PORT:-8000} --workers=2 --timeout=60 \
  --limit-request-line 16384 \
  --limit-request-field_size 0 \
  --limit-request-fields 200 \
  app:app