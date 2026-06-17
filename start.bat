@echo off
title SPADA UMG - Sistem Pembelajaran Daring UMG
color 0B

echo ============================================
echo    SPADA UMG - START SERVER
echo    Sistem Pembelajaran Daring UMG
echo ============================================
echo.

cd /d "%~dp0"

echo [1/3] Setup database...
python manage.py migrate --run-syncdb

echo.
echo [2/3] Selesai. Server siap dijalankan.
echo.

echo ============================================
echo    Server akan berjalan di:
echo    http://localhost:8000
echo    http://127.0.0.1:8000
echo ============================================
echo.
echo    CTRL+C untuk menghentikan server
echo.

python manage.py runserver 0.0.0.0:8000

pause
