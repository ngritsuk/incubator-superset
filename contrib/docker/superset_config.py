# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import os
from flask_appbuilder.security.manager import AUTH_DB, AUTH_OAUTH
from celery.schedules import crontab
from werkzeug.contrib.cache import RedisCache


def get_env_variable(var_name, default=None):
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = 'The environment variable {} was missing, abort...'\
                        .format(var_name)
            raise EnvironmentError(error_msg)


POSTGRES_USER = get_env_variable('POSTGRES_USER')
POSTGRES_PASSWORD = get_env_variable('POSTGRES_PASSWORD')
POSTGRES_HOST = get_env_variable('POSTGRES_HOST')
POSTGRES_PORT = get_env_variable('POSTGRES_PORT')
POSTGRES_DB = get_env_variable('POSTGRES_DB')
GOOGLE_OAUTH_KEY = get_env_variable('GOOGLE_OAUTH_KEY')
GOOGLE_OAUTH_SECRET = get_env_variable('GOOGLE_OAUTH_SECRET')

REDIS_HOST = get_env_variable('REDIS_HOST')
REDIS_PORT = get_env_variable('REDIS_PORT')


class CeleryConfig(object):
    BROKER_URL = 'redis://%s:%s/0' % (REDIS_HOST, REDIS_PORT)
    CELERY_IMPORTS = (
        'superset.sql_lab',
        'superset.tasks',
    )
    CELERY_RESULT_BACKEND = 'redis://%s:%s/1' % (REDIS_HOST, REDIS_PORT)

    #CELERYD_LOG_LEVEL = 'DEBUG'
    #CELERYD_PREFETCH_MULTIPLIER = 1
    #CELERY_ACKS_LATE = True

    CELERY_TASK_PROTOCOL = 1
    CELERY_ANNOTATIONS = {
        'sql_lab.get_sql_results': {
            'rate_limit': '100/s',
        },
        'email_reports.send': {
            'rate_limit': '1/s',
            'time_limit': 120,
            'soft_time_limit': 150,
            'ignore_result': True,
        },
    }
    CELERYBEAT_SCHEDULE = {
        'email_reports.schedule_hourly': {
            'task': 'email_reports.schedule_hourly',
            'schedule': crontab(minute=1, hour='*'),
        },
        'cache-warmup-hourly': {
            'task': 'cache-warmup',
            'schedule': crontab(minute=0, hour='*'),
            'kwargs': {
                'strategy_name': 'top_n_dashboards',
                'top_n': 3,
                'since': '7 days ago',
            },
        },
    }

# config
#SECRET_KEY = '\2\1fmfmanalytics$3cr3t$\1\2\e\y\y\h'  # noqa

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = 'postgresql://%s:%s@%s:%s/%s' % (POSTGRES_USER,
                                                           POSTGRES_PASSWORD,
                                                           POSTGRES_HOST,
                                                           POSTGRES_PORT,
                                                           POSTGRES_DB)

CELERY_CONFIG = CeleryConfig

OAUTH_PROVIDERS = [
 {
   'name': 'google',
   'whitelist': ['@facemetrics.io'],
   'icon': 'fa-google',
   'token_key': 'access_token', 
   'remote_app': {
     'base_url': 'https://www.googleapis.com/oauth2/v2/',
     'request_token_params': {
     'scope': 'email profile'
     },
     'request_token_url': None,
     'access_token_url':    'https://accounts.google.com/o/oauth2/token',
     'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
     'consumer_key': GOOGLE_OAUTH_KEY,
     'consumer_secret': GOOGLE_OAUTH_SECRET
    }
  }
]

AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Public"
RESULTS_BACKEND = RedisCache(
    host=REDIS_HOST, port=REDIS_PORT, key_prefix='superset_results')


# cache
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 24, # 1 day default (in secs)
    'CACHE_KEY_PREFIX': 'superset_results',
    'CACHE_REDIS_URL': CeleryConfig.BROKER_URL,
}


# email reports
ENABLE_SCHEDULED_EMAIL_REPORTS=True
EMAIL_REPORTS_CRON_RESOLUTION = 15
SCHEDULED_EMAIL_DEBUG_MODE = False

WEBDRIVER_BASEURL = get_env_variable('WEBDRIVER_BASEURL', 'http://0.0.0.0:8088/')
WEBDRIVER_WINDOW = '{"dashboard": (3000, 2000), "slice": (3000, 1200)}'

EMAIL_NOTIFICATIONS = True
SMTP_HOST = get_env_variable('SMTP_HOST', 'localhost')
SMTP_USER = get_env_variable('SMTP_USER', 'superset')
SMTP_PASSWORD = get_env_variable('SMTP_PASSWORD')
SMTP_STARTTLS = False
SMTP_SSL = True
SMTP_PORT = 465
SMTP_MAIL_FROM = SMTP_USER
