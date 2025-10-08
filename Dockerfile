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

# Expose port (Railway uses dynamic PORT)
EXPOSE $PORT

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Use startup script as default command
CMD ["/app/start.sh"]
