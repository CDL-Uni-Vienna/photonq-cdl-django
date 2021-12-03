# cdl-django-webservice

Required env variables:

POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD

DJANGO_SECRET_KEY
DATABASE_URL

# How to run it locally:

## Setup

Install python3.9
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
python3 manage.py makemigrations
python3 manage.py migrate
# admin web-interface available via /admin
python3 manage.py createsuperuser (define email, name, and password)

## How to start
python3 manage.py runserver 0.0.0.0:8080