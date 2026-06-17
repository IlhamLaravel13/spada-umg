import django, os, sys
os.environ['DJANGO_SETTINGS_MODULE']='spada_umg.settings'
django.setup()
from django.core.management import call_command
call_command('check', verbosity=0)
print('CHECK OK', flush=True)
sys.exit(0)
