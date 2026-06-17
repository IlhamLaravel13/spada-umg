try {
    $env:PYTHONUNBUFFERED = "1"
    $env:CYGWIN = "nodosfilewarning"
    
    Set-Location "C:\Users\Axioo Hype 1\OneDrive\Dokumen\spada_umg"
    
    # Install requirements if needed
    Write-Output "Menginstall dependencies..."
    pip install -r requirements.txt 2>&1 | Out-Null
    
    # Run migrations
    Write-Output "Migrasi database..."
    python -c "
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'spada_umg.settings'
sys.path.insert(0, '.')
import django
django.setup()
from django.core.management import call_command
call_command('migrate', '--run-syncdb', verbosity=0)
print('Database siap!')
"
    
    # Start server
    Write-Output ""
    Write-Output "============================================"
    Write-Output "  SPADA UMG - Server Berjalan!"
    Write-Output "  http://localhost:8000"
    Write-Output "  http://127.0.0.1:8000"
    Write-Output "============================================"
    Write-Output ""
    
    python manage.py runserver 0.0.0.0:8000
    
} catch {
    Write-Error "Error: $_"
    Read-Host "Tekan Enter untuk keluar"
}
