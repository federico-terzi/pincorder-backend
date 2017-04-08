from .settings import *

DEBUG = False

ALLOWED_HOSTS = ['pincorder.freddytstudio.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pincorder',
	'USER': DB_USER,
	'PASSWORD': DB_PASSWORD,
	'HOST': 'localhost',
	'PORT': '',
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')