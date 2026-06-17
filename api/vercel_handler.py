import os
import sys
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spada_umg.settings')

os.environ['VERCEL'] = 'true'

application = get_wsgi_application()


def handler(request):
    return application(request)
