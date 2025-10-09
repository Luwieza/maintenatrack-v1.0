#!/bin/bash

# Railway startup script for MaintenaTrack
echo "🚀 Starting MaintenaTrack on Railway..."

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional)
echo "👤 Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@maintenatrack.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('ℹ️  Superuser already exists')
" || echo "⚠️  Superuser creation skipped"

# Debug environment
echo "🔍 PORT environment variable: ${PORT:-'not set, using 8000'}"
echo "🔍 Django settings: ${DJANGO_SETTINGS_MODULE:-'not set'}"

# Start Gunicorn
echo "🌐 Starting Gunicorn server on port ${PORT:-8000}..."
exec gunicorn maintenatrack.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile -