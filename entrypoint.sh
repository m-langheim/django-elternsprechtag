#!/bin/bash

# python manage.py collectstatic --no-input
# i commit my migration files to git so i dont need to run it on server
# ./manage.py makemigrations app_name
python manage.py migrate --no-input

# Create Admin account
# DJANGO_SUPERUSER_PASSWORD=$SUPER_USER_PASSWORD python manage.py createsuperuser --email $SUPER_USER_EMAIL --noinput

python manage.py runserver 0.0.0.0:8000

# gunicorn django_project.wsgi:application --bind 0.0.0.0:8000

# here it start nginx and the uwsgi
# supervisord -c /etc/supervisor/supervisord.conf -n