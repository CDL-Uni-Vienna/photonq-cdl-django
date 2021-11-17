from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-#8yff&k+w1)+!&$+u5bih2px#o9yh!9g=36_y5k8+_r9czp!gg"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

BASE_URL = "http://localhost:8000"

try:
    from .local import *
except ImportError:
    pass
