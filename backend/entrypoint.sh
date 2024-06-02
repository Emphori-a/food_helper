#!/bin/bash

python manage.py makemigrations
python manage.py migrate
python manage.py load_csv_data ingredients.csv
python manage.py load_csv_data tags.csv
python manage.py collectstatic --no-input
gunicorn --bind 0.0.0.0:8080 foodgram_backend.wsgi