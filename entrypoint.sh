#!/bin/bash

# python manage.py collectstatic --no-input
# i commit my migration files to git so i dont need to run it on server
# ./manage.py makemigrations app_name
# while ! mysqladmin ping -h"$DB_HOST" --silent; do
#     sleep 1
# done

python manage.py migrate --settings=elternsprechtag.settings.production --no-input

# Create Admin account
DJANGO_SUPERUSER_PASSWORD=$SUPER_USER_PASSWORD python manage.py createsuperuser --settings=elternsprechtag.settings.production --noinput --skip-checks --email $SUPER_USER_EMAIL

# Start the production server for Django

gunicorn elternsprechtag.wsgi:application --bind 0.0.0.0:8000 --env DJANGO_SETTINGS_MODULE=elternsprechtag.settings.production -c gunicorn.conf.py --log-config log.conf
# python manage.py runserver 0.0.0.0:8000 --settings=elternsprechtag.settings.production
