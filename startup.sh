#!/bin/sh
set -eu

pip install --quiet --disable-pip-version-check -r requirements.txt

exec gunicorn --bind=0.0.0.0:${PORT:-8000} app:app