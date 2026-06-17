#!/bin/bash
echo "===== SPADA UMG Build Script ====="
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "===== Build Complete ====="
