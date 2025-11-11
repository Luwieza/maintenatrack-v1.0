#!/bin/bash

# Railway startup script for MaintenaTrack
echo "🚀 Starting MaintenaTrack on Railway..."

# Set production settings
export DJANGO_SETTINGS_MODULE="maintenatrack.settings_prod"
echo "🔧 Using production settings: $DJANGO_SETTINGS_MODULE"

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional)
echo "👤 Creating superuser if needed..."
# Wait a moment for database to be fully ready
sleep 2
python manage.py shell -c "
from django.contrib.auth.models import User
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@maintenatrack.com', 'admin123')
        print('✅ Superuser created: admin/admin123')
    else:
        print('ℹ️  Superuser already exists')
        # Show existing admin user
        admin = User.objects.get(username='admin')
        print(f'ℹ️  Admin user ID: {admin.id}, Active: {admin.is_active}')
except Exception as e:
    print(f'❌ Error creating superuser: {e}')
" || echo "⚠️  Superuser creation failed"

# Also create via environment variables if available
echo "👤 Creating additional superuser via environment..."
python manage.py shell -c "
from django.contrib.auth.models import User
import os
username = os.environ.get('ADMIN_USERNAME', 'maintenatrack')
email = os.environ.get('ADMIN_EMAIL', 'admin@maintenatrack.com')  
password = os.environ.get('ADMIN_PASSWORD', 'MaintenaTrack2025!')
try:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f'✅ Additional superuser created: {username}/{password}')
    else:
        print(f'ℹ️  User {username} already exists')
except Exception as e:
    print(f'❌ Error creating additional superuser: {e}')
" || echo "⚠️  Additional superuser creation failed"

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