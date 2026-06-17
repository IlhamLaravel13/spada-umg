#!/bin/bash
# SPADA UMG - Build Script for Vercel Deployment
echo "===== SPADA UMG Build Script ====="

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput --clear

# Run migrations
python manage.py migrate --noinput

# Create cache table
python manage.py createcachetable

# Notify build success
echo "===== Build Complete ====="
