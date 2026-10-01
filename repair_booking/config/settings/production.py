import os

import dj_database_url

from .base import *

DEBUG = False
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
SECRET_KEY = os.environ["SECRET_KEY"]

render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
allowed_hosts = os.getenv("ALLOWED_HOSTS", render_hostname)
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

DATABASES = {
	"default": dj_database_url.parse(
		os.environ["DATABASE_URL"],
		conn_max_age=600,
		ssl_require=True,
	)
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
