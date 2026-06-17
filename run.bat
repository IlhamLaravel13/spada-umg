@echo off
cd /d "C:\Users\Axioo Hype 1\OneDrive\Dokumen\spada_umg"
echo Menjalankan SPADA UMG Server...
start "SPADA UMG" pythonw manage.py runserver 0.0.0.0:8000 --noreload
echo Server berjalan di http://localhost:8000
echo.
echo Tekan sembarang tombol untuk membuka browser...
pause >nul
start http://localhost:8000
