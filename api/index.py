import os
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spada_umg.settings')
os.environ['VERCEL'] = 'true'

try:
    from django.core.wsgi import get_wsgi_application
    from whitenoise import WhiteNoise
    from django.conf import settings

    _app = get_wsgi_application()
    _static_root = str(settings.STATIC_ROOT)
    app = WhiteNoise(_app, root=_static_root)
except Exception:
    error_trace = traceback.format_exc()

    def app(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [f'Django init failed:\n\n{error_trace}'.encode()]
