#!/bin/bash
echo "===== SPADA UMG Build Script ====="
echo "Running migrations..."
python manage.py migrate --run-syncdb --noinput
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "===== Build Complete ====="
