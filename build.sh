#!/usr/bin/env bash
# Render runs this on every deploy.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
# Creates the evaluator test login, or resets its password, from DJANGO_SUPERUSER_* env vars.
python manage.py shell -c "
import os
from django.contrib.auth.models import User
user, _ = User.objects.get_or_create(username=os.environ['DJANGO_SUPERUSER_USERNAME'])
user.email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
user.is_staff = user.is_superuser = True
user.set_password(os.environ['DJANGO_SUPERUSER_PASSWORD'])
user.save()
"
