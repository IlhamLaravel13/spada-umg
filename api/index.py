import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spada_umg.settings')
os.environ['VERCEL'] = 'true'

try:
    from django.core.wsgi import get_wsgi_application
    app = get_wsgi_application()
except Exception:
    error_trace = traceback.format_exc()

    def app(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [f'Django init failed:\n\n{error_trace}'.encode()]
