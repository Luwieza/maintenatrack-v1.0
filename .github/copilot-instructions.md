# MaintenaTrack AI Coding Agent Instructions

## Project Overview

**MaintenaTrack** is a Django 5.2 web application for tracking industrial equipment maintenance activities in a 22-zone facility. Core workflow: technicians log maintenance incidents with alarm codes, zone locations, difficulty levels, and sequential troubleshooting steps.

## Architecture & Key Components

### Data Model (`maintenance/models.py`)

Three core models with specific relationships:

- **Equipment**: Assets with unique `asset_tag` (nullable) and mandatory `zone` (1-22). Constraint: `unique_equipment_name_per_zone`
- **MaintenanceLog**: Central entity. Can link to Equipment OR standalone with zone. Has `difficulty` (Easy/Medium/Hard), `alarm_code`, `lam_checked` boolean, and `description`
- **Step**: Inline ordered steps per log. Constraint: `unique_step_order_per_log`. Fields: `order`, `action`, `result`, `duration_minutes`, `performed_by`

**Critical pattern**: If log has equipment, zone auto-inherits from equipment (see `MaintenanceLog.clean()` and admin `save_model()`)

### Forms & Formsets (`maintenance/forms.py`)

- **StepFormSet**: Uses `inlineformset_factory` with `extra=3`, `can_delete=False`, `min_num=0`
- **Custom validation**: Empty step forms (no action) are automatically cleared in `StepForm.clean()`. Non-empty forms without `order` auto-populate from formset index
- Steps are NOT individually deletable in forms—use admin or programmatic deletion

### Views (`maintenance/views.py`)

Key patterns:

1. **log_create/log_update**: Use formset pattern. On update, **existing steps are deleted** then recreated (`log.steps.all().delete()`) to avoid constraint violations
2. **add_equipment**: AJAX endpoint creates equipment with auto-generated `asset_tag` (format: `AUTO-{max_num+1}`). Returns JSON for modal integration
3. **Filtering**: `log_list` supports `q` (full-text search across alarm/description/steps), `zone`, `difficulty`, `my_logs` query params
4. **Permissions**: Only log creator can edit/delete their logs (checked in `log_update`/`log_delete`)

### Admin (`maintenance/admin.py`)

- **StepInline**: Tabular inline for editing steps within log
- **Custom action**: `mark_lam_checked` bulk action
- Auto-assigns `created_by` and zone defaults in `save_model()`
- Query optimization: `select_related` in `get_queryset()`

### Templates & Frontend

- **No frontend framework**: Vanilla JavaScript with inline `<script>` tags
- **Equipment modal**: In `log_form.html`, button triggers modal that POSTs to `/equipment/add/` endpoint, then dynamically updates `<select>` dropdown
- **Base template**: Custom CSS with J&J branding (`--jj-red: #e4002b`), background image from `static/maintenance/img/product.png`
- Static files served via **WhiteNoise** middleware

## Development Workflow

### Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Running with Docker

```bash
docker-compose up --build  # Dev with live reload
docker-compose -f docker-compose.prod.yml up  # Gunicorn production
```

### Database

- **SQLite** (`db.sqlite3`) for dev/testing
- Migrations in `maintenance/migrations/`
- **No tests written yet** (`tests.py` is empty stub)

### Static Files

- `python manage.py collectstatic` gathers to `staticfiles/`
- Already run in Dockerfile, safe to re-run locally

## Critical Conventions

### Zone Validation

- Zone is PositiveSmallIntegerField with validators: `MinValueValidator(1)`, `MaxValueValidator(22)`
- **Always enforce 1-22 range** in forms, views, and migrations

### Step Order Management

- Order is NOT auto-incremented by database
- Forms auto-populate order from formset index if missing
- When manually creating steps, **always** provide `order` or risk constraint violations

### User Assignment

- `created_by` and `performed_by` are SET_NULL (nullable FKs to User)
- Admin auto-assigns current user if null
- Views manually set `log.created_by = request.user` on create

### Equipment Auto-Creation

- Quick add uses regex to find highest `AUTO-{num}` tag: `r'AUTO-(\d+)'`
- If IntegrityError (name+zone exists), returns existing equipment instead of failing
- Zone defaults to `1` for quick-adds—users should update in admin

### Formset Validation Pattern

When editing logs with steps:

1. Validate both form and formset
2. Save parent log first
3. **Delete all existing steps**: `log.steps.all().delete()`
4. Iterate formset, skip empty forms (no action)
5. Manually set `log`, `order`, `performed_by` before saving each step

## URL Patterns

- Root namespace: `maintenance:`
- Auth: Django's built-in `/accounts/login/`, custom `/accounts/signup/`
- Logs: `/logs/`, `/logs/new/`, `/logs/<pk>/`, `/logs/<pk>/edit/`, `/logs/<pk>/delete/`
- Equipment: `/equipment/add/` (AJAX), `/equipment/<pk>/delete/`

## Settings (`maintenatrack/settings.py`)

- `DEBUG = True` (hardcoded for dev)
- `TIME_ZONE = "Europe/Dublin"`
- `ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']`
- Auth redirects: `LOGIN_REDIRECT_URL = "maintenance:log_list"`, `LOGOUT_REDIRECT_URL = "login"`

## When Adding Features

- **New fields**: Consider zone constraints, null handling, and admin autocomplete
- **New views**: Add `@login_required` if modifying data, use `require_http_methods` decorator
- **Formsets**: Always handle empty forms, ensure order uniqueness
- **Equipment**: Remember `asset_tag` is unique but nullable—handle None cases
- **Queries**: Use `select_related`/`prefetch_related` for Equipment/User/Steps to avoid N+1

## Debugging Notes

- Check `created_by` null handling—admin sets it, but views must too
- Step constraint violations? Delete before recreating or ensure unique (log, order) pairs
- Zone validation errors? Ensure 1-22 range in forms and models
- Equipment modal not working? Check CSRF token in template and AJAX headers
