#!/bin/bash

python manage.py makemigrations
python manage.py migrate
python manage.py load_csv_data ingredients.csv
python manage.py load_csv_data tags.csv
gunicorn --bind 0.0.0.0:8080 foodgram_backend.wsgi