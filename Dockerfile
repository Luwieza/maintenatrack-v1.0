# Python slim image
FROM python:3.12-slim

# Prevent .pyc, set non-interactive
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Workdir
WORKDIR /app

# System deps (build + runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Django settings expect collectstatic in production; safe to run here too
RUN mkdir -p /app/staticfiles && \
    python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Default command (SQLite is fine)
# NOTE: for local testing you can also run "python manage.py runserver 0.0.0.0:8000"
CMD ["gunicorn", "maintenatrack.wsgi:application", "--bind", "0.0.0.0:8000"]
