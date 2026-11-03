#!/usr/bin/env bash
# Runs on Render every time the site is deployed.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py load_skills || echo "load_skills skipped"
python manage.py createsuperuser --no-input || echo "admin account already exists"