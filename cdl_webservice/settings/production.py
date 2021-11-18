"""
Django production settings for cdl_webservice project.

For more information on this file, see
https://docs.djangoproject.com/en/stable/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/stable/ref/settings/

This development settings are unsuitable for production, see
https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
"""

import random
import string

import dj_database_url
import django_cache_url

from .base import *  # noqa

# > Debug Switch
# SECURITY WARNING: don't run with debug turned on in production!
# IMPORTANT: Specified in the environironment or set to default (off).
# See https://docs.djangoproject.com/en/stable/ref/settings/#debug
DEBUG = os.environ.get("DJANGO_DEBUG", "off") == "on"

# > DEBUG_PROPAGATE_EXCEPTIONS Switch
# SECURITY WARNING: don't run with debug turned on in production!
# IMPORTANT: Specified in the environironment or set to default (off).
# See https://docs.djangoproject.com/en/stable/ref/settings/#debug
DEBUG_PROPAGATE_EXCEPTIONS = (
    os.environ.get("DJANGO_DEBUG_PROPAGATE_EXCEPTIONS", "off") == "on"
)

# This is used by Wagtail's email notifications for constructing absolute
# URLs. Please set to the domain that users will access the admin site.
if "PRIMARY_HOST" in os.environ:
    BASE_URL = "https://{}".format(os.environ["PRIMARY_HOST"])

# > Secret Key
# SECURITY WARNING: keep the secret key used in production secret!
# IMPORTANT: Specified in the environironment or generate an ephemeral key.
# See https://docs.djangoproject.com/en/stable/ref/settings/#secret-key
if "DJANGO_SECRET_KEY" in os.environ:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    # Use if/else rather than a default value to avoid calculating this,
    # if we don't need it.
    print(
        "WARNING: DJANGO_SECRET_KEY not found in os.os.environiron. Generating ephemeral SECRET_KEY."
    )
    SECRET_KEY = "".join(
        [random.SystemRandom().choice(string.printable) for i in range(50)]
    )


# > SSL Redirect
# Every rquest gets redirected to HTTPS
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "off") == "on"

# > Allowed Hosts
# Accept all hostnames, since we don't know in advance
# which hostname will be used for any given Docker instance.
# IMPORTANT: Set this to a real hostname when using this in production!
# See https://docs.djangoproject.com/en/stable/ref/settings/#allowed-hosts
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(";")

# Set s-max-age header that is used by reverse proxy/front end cache. See
# urls.py.
try:
    CACHE_CONTROL_S_MAXAGE = int(os.environ.get("CACHE_CONTROL_S_MAXAGE", 600))
except ValueError:
    pass

# Give front-end cache 30 second to revalidate the cache to avoid hitting the
# backend. See urls.py.
CACHE_CONTROL_STALE_WHILE_REVALIDATE = int(
    os.environ.get("CACHE_CONTROL_STALE_WHILE_REVALIDATE", 30)
)

# > Security Configuration
# This configuration is required to achieve good security rating.
# You can test it using https://securityheaders.com/
# https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security

# > Force HTTPS Redirect
# https://docs.djangoproject.com/en/stable/ref/settings/#secure-ssl-redirect
if os.environ.get("SECURE_SSL_REDIRECT", "true").strip().lower() == "true":
    SECURE_SSL_REDIRECT = False

# This will allow the cache to swallow the fact that the website is behind TLS
# and inform the Django using "X-Forwarded-Proto" HTTP header.
# https://docs.djangoproject.com/en/stable/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# This is a setting setting HSTS header. This will enforce the visitors to use
# HTTPS for an amount of time specified in the header. Please make sure you
# consult with sysadmin before setting this.
# https://docs.djangoproject.com/en/stable/ref/settings/#secure-hsts-seconds
if "SECURE_HSTS_SECONDS" in os.environ:
    SECURE_HSTS_SECONDS = int(os.environ["SECURE_HSTS_SECONDS"])

# https://docs.djangoproject.com/en/stable/ref/settings/#secure-browser-xss-filter
if os.environ.get("SECURE_BROWSER_XSS_FILTER", "true").lower().strip() == "true":
    SECURE_BROWSER_XSS_FILTER = True

# https://docs.djangoproject.com/en/stable/ref/settings/#secure-content-type-nosniff
if os.environ.get("SECURE_CONTENT_TYPE_NOSNIFF", "true").lower().strip() == "true":
    SECURE_CONTENT_TYPE_NOSNIFF = True

# > Email Settings
# We use SMTP to send emails. We typically use transactional email services
# that let us use SMTP.
# https://docs.djangoproject.com/en/2.1/topics/email/

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host
if "DJANGO_EMAIL_HOST" in os.environ:
    EMAIL_HOST = os.environ["DJANGO_EMAIL_HOST"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-port
if "DJANGO_EMAIL_PORT" in os.environ:
    try:
        EMAIL_PORT = int(os.environ["DJANGO_EMAIL_PORT"])
    except ValueError:
        pass

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host-user
if "DJANGO_EMAIL_HOST_USER" in os.environ:
    EMAIL_HOST_USER = os.environ["DJANGO_EMAIL_HOST_USER"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host-password
if "DJANGO_EMAIL_HOST_PASSWORD" in os.environ:
    EMAIL_HOST_PASSWORD = os.environ["DJANGO_EMAIL_HOST_PASSWORD"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-use-tls
if os.environ.get("DJANGO_EMAIL_USE_TLS", "false").lower().strip() == "true":
    EMAIL_USE_TLS = True

# https://docs.djangoproject.com/en/stable/ref/settings/#email-use-ssl
if os.environ.get("DJANGO_EMAIL_USE_SSL", "false").lower().strip() == "true":
    EMAIL_USE_SSL = True

# https://docs.djangoproject.com/en/stable/ref/settings/#email-subject-prefix
if "DJANGO_EMAIL_SUBJECT_PREFIX" in os.environ:
    EMAIL_SUBJECT_PREFIX = os.environ["DJANGO_EMAIL_SUBJECT_PREFIX"]

# SERVER_EMAIL is used to send emails to administrators.
# https://docs.djangoproject.com/en/stable/ref/settings/#server-email
# DEFAULT_FROM_EMAIL is used as a default for any mail send from the website to
# the users.
# https://docs.djangoproject.com/en/stable/ref/settings/#default-from-email
if "DJANGO_SERVER_EMAIL" in os.environ:
    SERVER_EMAIL = DEFAULT_FROM_EMAIL = os.environ["DJANGO_SERVER_EMAIL"]

# > Database Configuration
# See https://pypi.org/project/dj-database-url/
# See https://docs.djangoproject.com/en/stable/ref/settings/#databases
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES["default"].update(db_from_env)

# Configure caches from cache url
CACHES = {"default": django_cache_url.config()}


# > Logging
# This logging is configured to be used with Sentry and console logs. Console
# logs are widely used by platforms offering Docker deployments, e.g. Heroku.
# We use Sentry to only send error logs so we're notified about errors that are
# not Python exceptions.
# We do not use default mail or file handlers because they are of no use for
# us.
# https://docs.djangoproject.com/en/stable/topics/logging/
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        # Send logs with at least INFO level to the console.
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # Send logs with level of at least ERROR to Sentry.
        #'sentry': {
        #    'level': 'ERROR',
        #    'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        # },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s][%(process)d][%(levelname)s][%(name)s] %(message)s"
        }
    },
    "loggers": {
        "esite": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "wagtail": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
