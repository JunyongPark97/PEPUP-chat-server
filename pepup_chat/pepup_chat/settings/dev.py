
from pepup_chat.settings.base import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'z=9e@x4iz^x=w$ktgkjgis8o_2h&(^4_kb5r_#r77))04m%&k%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '../../db.sqlite3'),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/


SETTING_PRD_DIC = load_credential("production")

# # AWS
AWS_ACCESS_KEY_ID = SETTING_PRD_DIC['S3']['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = SETTING_PRD_DIC['S3']['AWS_SECRET_ACCESS_KEY']
AWS_DEFAULT_ACL = SETTING_PRD_DIC['S3']['AWS_DEFAULT_ACL']
AWS_S3_REGION_NAME = SETTING_PRD_DIC['S3']['AWS_S3_REGION_NAME']
AWS_S3_SIGNATURE_VERSION = SETTING_PRD_DIC['S3']['AWS_S3_SIGNATURE_VERSION']
AWS_STORAGE_BUCKET_NAME = SETTING_PRD_DIC['S3']['AWS_STORAGE_BUCKET_NAME']

AWS_QUERYSTRING_AUTH = False
AWS_S3_HOST = 's3.%s.amazonaws.com' % AWS_S3_REGION_NAME

AWS_S3_CUSTOM_DOMAIN = '%s.s3.%s.amazonaws.com' % (AWS_STORAGE_BUCKET_NAME,AWS_S3_REGION_NAME)

STATIC_LOCATION = 'static'
STATIC_URL = "https://%s/%s/" % (AWS_S3_HOST, STATIC_LOCATION)
STATICFILES_STORAGE = 'pepup.storage.StaticStorage'

MEDIA_LOCATION = 'media'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_HOST,MEDIA_LOCATION)

# TODO : ADD in prod.py
DEFAULT_FILE_STORAGE = 'pepup.storage.CustomS3Boto3Storage'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_ROOT = "https://%s/static/" % AWS_S3_CUSTOM_DOMAIN
MEDIA_ROOT = "https://%s/media/" % AWS_S3_CUSTOM_DOMAIN

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "landing", "static"),
)


# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
