#!/bin/bash

# python manage.py collectstatic --no-input
# i commit my migration files to git so i dont need to run it on server
# ./manage.py makemigrations app_name
python manage.py migrate --settings=elternsprechtag.settings.production --no-input

# Create Admin account
DJANGO_SUPERUSER_PASSWORD=$SUPER_USER_PASSWORD python manage.py --settings=elternsprechtag.settings.production createsuperuser --noinput --skip-checks --email $SUPER_USER_EMAIL

# Start the production server for Django

gunicorn elternsprechtag.wsgi:application --bind 0.0.0.0:8000