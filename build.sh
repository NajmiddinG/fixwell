#!/usr/bin/env bash

set -o errexit

export DJANGO_SETTINGS_MODULE=repair_booking.config.settings.production

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input