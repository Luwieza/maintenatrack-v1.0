"""
Views for MaintenaTrack.

- log_list: searchable, paginated list of maintenance logs.
- log_detail: detail page with steps.
- log_create: create a log with inline steps (login required).
- add_equipment: AJAX endpoint to add new equipment without admin.
- signup: simple user registration.
- home/about: static pages.
"""

from typing import Any, Dict
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    # Fallback if django-ratelimit is not installed
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .forms import MaintenanceLogForm, StepFormSet
from .models import MaintenanceLog, Equipment


@require_http_methods(["GET"])
def log_list(request: HttpRequest) -> HttpResponse:
    """List logs with optional filters."""
    q = request.GET.get("q", "").strip()
    zone = request.GET.get("zone", "").strip()
    diff = request.GET.get("difficulty", "").strip()
    my_logs = request.GET.get("my_logs", "").strip()
    page_number = request.GET.get("page", "1")

    qs = (
        MaintenanceLog.objects
        .select_related("equipment", "created_by")
        .order_by("-created_at")
    )

    if q:
        qs = qs.filter(
            Q(alarm_code__icontains=q)
            | Q(alarm_name__icontains=q)
            | Q(description__icontains=q)
            | Q(steps__action__icontains=q)
            | Q(steps__result__icontains=q)
            | Q(equipment__name__icontains=q)
            | Q(equipment__asset_tag__icontains=q)
            | Q(created_by__username__icontains=q)
            | Q(created_by__first_name__icontains=q)
            | Q(created_by__last_name__icontains=q)
        ).distinct()

    if zone:
        # Zone is now a CharField, so filter by exact match (case-insensitive)
        qs = qs.filter(zone__iexact=zone)

    if diff:
        qs = qs.filter(difficulty=diff)

    # Filter for user's own logs only
    if my_logs == "true" and request.user.is_authenticated:
        qs = qs.filter(created_by=request.user)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)

    return render(request, "maintenance/log_list.html", {
        "page_obj": page_obj,
        "logs": page_obj.object_list,
        "q": q,
        "zone": zone,
        "difficulty": diff,
        "my_logs": my_logs,
    })


@require_http_methods(["GET"])
def log_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Show a single log and its related steps and metadata."""
    log = get_object_or_404(
        MaintenanceLog.objects
        .select_related("equipment", "created_by")
        .prefetch_related("steps"),
        pk=pk,
    )
    return render(request, "maintenance/log_detail.html", {"log": log})


@ratelimit(key='user', rate='10/m', method='POST', block=True)
@login_required
@require_http_methods(["GET", "POST"])
def log_create(request: HttpRequest) -> HttpResponse:
    """Create a new maintenance log with inline steps (formset)."""
    if request.method == "POST":
        form = MaintenanceLogForm(request.POST)
        formset = StepFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                log = form.save(commit=False)

                # Auto-fill zone if blank
                if not log.zone and log.equipment and log.equipment.zone:
                    log.zone = log.equipment.zone

                log.created_by = request.user
                log.save()

                # Save only non-empty steps with improved validation
                formset.instance = log
                saved_steps = []
                for step_form in formset:
                    if (step_form.cleaned_data and
                        step_form.cleaned_data.get('action') and
                            step_form.cleaned_data.get('action').strip()):
                        step = step_form.save(commit=False)
                        step.log = log
                        if not step.order:
                            step.order = len(saved_steps) + 1
                        if not step.performed_by:
                            step.performed_by = request.user
                        step.save()
                        saved_steps.append(step)

                # Add success message
                messages.success(
                    request, f'✅ Log "{log.alarm_code}" saved successfully with {len(saved_steps)} steps!')
                return redirect('maintenance:log_detail', pk=log.pk)

            except Exception as e:
                messages.error(request, f'❌ Error saving log: {str(e)}')
                # Re-populate form with submitted data
        else:
            # Handle form validation errors
            error_messages = []
            if not form.is_valid():
                for field, errors in form.errors.items():
                    error_messages.extend(
                        [f'{field}: {error}' for error in errors])
            if not formset.is_valid():
                error_messages.append(
                    'Please check the steps section for errors.')

            if error_messages:
                messages.error(
                    request, f'❌ Please fix the following errors: {"; ".join(error_messages)}')

    else:
        form = MaintenanceLogForm()
        formset = StepFormSet()

    return render(request, "maintenance/log_form.html", {
        "form": form, "formset": formset
    })


@login_required
@require_http_methods(["POST"])
def add_equipment(request: HttpRequest) -> HttpResponse:
    """
    AJAX endpoint to create new equipment without admin.
    Form provides 'name' and 'zone', we auto-fill other required fields.
    """
    name = request.POST.get("name", "").strip()
    zone = request.POST.get("zone", "1").strip()

    if not name:
        return JsonResponse({"error": "Name is required."}, status=400)

    if not zone:
        return JsonResponse({"error": "Zone is required."}, status=400)

    # Validate and sanitize zone
    import re
    zone = re.sub(r'[^\w\-\_]', '', zone)
    if len(zone) > 10:
        return JsonResponse({"error": "Zone must be 10 characters or less."}, status=400)
    if len(zone) == 0:
        return JsonResponse({"error": "Zone cannot be empty."}, status=400)

    zone = zone.upper()  # Normalize to uppercase

    # Generate unique asset tag by finding the highest existing AUTO- number
    import re
    from django.db import IntegrityError

    existing_tags = Equipment.objects.filter(
        asset_tag__startswith="AUTO-"
    ).values_list('asset_tag', flat=True)

    max_num = 0
    for tag in existing_tags:
        match = re.search(r'AUTO-(\d+)', tag)
        if match:
            max_num = max(max_num, int(match.group(1)))

    try:
        equipment = Equipment.objects.create(
            name=name,
            asset_tag=f"AUTO-{max_num + 1}",  # unique asset tag
            zone=zone,  # use provided zone
            status=Equipment.Status.ACTIVE,
        )
        return JsonResponse({
            "id": equipment.id,
            "name": equipment.name,
            "zone": equipment.zone,
        })
    except IntegrityError:
        # Equipment with this name and zone already exists
        # Return the existing equipment instead
        equipment = Equipment.objects.filter(name=name, zone=zone).first()
        if equipment:
            return JsonResponse({
                "id": equipment.id,
                "name": equipment.name,
                "zone": equipment.zone,
                "message": "Equipment already exists, using existing entry."
            })
        else:
            return JsonResponse({
                "error": "Equipment with this name already exists in this zone."
            }, status=400)


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@require_http_methods(["GET", "POST"])
def signup(request: HttpRequest) -> HttpResponse:
    """Register a new user and log them in, then redirect to the log list."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Account created. Welcome!")
            return redirect("maintenance:log_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@require_http_methods(["GET"])
def home(request: HttpRequest) -> HttpResponse:
    """Simple landing page."""
    return render(request, "maintenance/home.html")


@require_http_methods(["GET"])
def about(request: HttpRequest) -> HttpResponse:
    """About page."""
    return render(request, "maintenance/about.html")


@login_required
@require_http_methods(["GET", "POST"])
def log_update(request: HttpRequest, pk: int) -> HttpResponse:
    """Update a maintenance log - only by the creator."""
    log = get_object_or_404(MaintenanceLog, pk=pk)

    # Check if user is the creator
    if log.created_by != request.user:
        messages.error(request, "You can only edit logs you created.")
        return redirect("maintenance:log_detail", pk=pk)

    if request.method == "POST":
        form = MaintenanceLogForm(request.POST, instance=log)
        formset = StepFormSet(request.POST, instance=log)

        if form.is_valid() and formset.is_valid():
            log = form.save()

            # Clear existing steps to avoid constraint violations
            log.steps.all().delete()

            # Save new steps
            saved_steps = []
            for step_form in formset:
                if (step_form.cleaned_data and
                    step_form.cleaned_data.get('action') and
                        step_form.cleaned_data.get('action').strip() and
                        not step_form.cleaned_data.get('DELETE', False)):
                    step = step_form.save(commit=False)
                    step.log = log
                    if not step.order:
                        step.order = len(saved_steps) + 1
                    if not step.performed_by:
                        step.performed_by = request.user
                    step.save()
                    saved_steps.append(step)

            messages.success(
                request, f"Maintenance log '{log.alarm_code}' updated successfully with {len(saved_steps)} step(s).")
            return redirect("maintenance:log_detail", pk=log.pk)
        else:
            # Add more detailed error messages for debugging
            if form.errors:
                for field, errors in form.errors.items():
                    field_name = form.fields[field].label if field in form.fields else field
                    for error in errors:
                        messages.error(request, f"{field_name}: {error}")

            if formset.errors:
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(
                                    request, f"Step {i+1} - {field}: {error}")

            if formset.non_form_errors():
                for error in formset.non_form_errors():
                    messages.error(request, f"Form error: {error}")

            # If no specific errors but form is still invalid
            if not form.errors and not formset.errors and not formset.non_form_errors():
                messages.error(
                    request, "Please check all required fields and try again.")

            # Add general message if there are errors
            messages.warning(
                request, "Please correct the errors below and try submitting again.")
    else:
        form = MaintenanceLogForm(instance=log)
        formset = StepFormSet(instance=log)

    return render(request, "maintenance/log_form.html", {
        "form": form,
        "formset": formset,
        "log": log,
        "is_update": True
    })


@login_required
@require_http_methods(["GET", "POST"])
def log_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a maintenance log - only by the creator."""
    log = get_object_or_404(MaintenanceLog, pk=pk)

    # Check if user is the creator
    if log.created_by != request.user:
        messages.error(request, "You can only delete logs you created.")
        return redirect("maintenance:log_detail", pk=pk)

    if request.method == "POST":
        log.delete()
        messages.success(request, "Maintenance log deleted successfully.")
        return redirect("maintenance:log_list")

    return render(request, "maintenance/log_confirm_delete.html", {"log": log})


@login_required
@require_http_methods(["POST"])
def equipment_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete equipment - only by users who created logs with it."""
    equipment = get_object_or_404(Equipment, pk=pk)

    # Check if user has any logs with this equipment
    user_logs_with_equipment = MaintenanceLog.objects.filter(
        equipment=equipment,
        created_by=request.user
    ).exists()

    if not user_logs_with_equipment:
        messages.error(
            request, "You can only delete equipment you've used in your logs.")
        return redirect("maintenance:log_list")

    # Check if other users have logs with this equipment
    other_users_logs = MaintenanceLog.objects.filter(
        equipment=equipment
    ).exclude(created_by=request.user).exists()

    if other_users_logs:
        messages.error(
            request, "Cannot delete equipment that other users have logged with.")
        return redirect("maintenance:log_list")

    equipment.delete()
    messages.success(
        request, f"Equipment '{equipment.name}' deleted successfully.")
    return redirect("maintenance:log_list")
