from .settings import *

INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'ckeditor',
    'ckeditor_uploader',
    'taggit',
    'import_export',
    'django_filters',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'cloudinary_storage',
    'cloudinary',
    'ai_assistant',
    'analytics',
    'api',
    'certificates',
    'library',
    'media_manager',
    'payments',
    'reports',
    'website_settings',
    'notifications',
]]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [m for m in MIDDLEWARE if 'allauth' not in m]

ROOT_URLCONF = 'test_urls'
