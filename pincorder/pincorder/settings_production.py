from .settings import *
import os

DEBUG = False

ALLOWED_HOSTS = ['pincorder.freddytstudio.com']

# Databases credentials are stored into ENV VARS

"""
To populate database credentials use:
export PINCORDER_DB_USER={YOUR_USER}
export PINCORDER_DB_PASSWORD={YOUR_PASSWORD}
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pincorder',
	'USER': os.environ['PINCORDER_DB_USER'],
	'PASSWORD': os.environ['PINCORDER_DB_PASSWORD'],
	'HOST': 'localhost',
	'PORT': '',
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')