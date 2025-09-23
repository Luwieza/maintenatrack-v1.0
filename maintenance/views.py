"""
Views for MaintenaTrack.

- log_list: searchable, paginated list of maintenance logs.
- log_detail: detail page with steps.
- log_create: create a log with inline steps (login required).
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
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import MaintenanceLogForm, StepFormSet
from .models import MaintenanceLog


@require_http_methods(["GET"])
def log_list(request: HttpRequest) -> HttpResponse:
    """
    List logs with optional filters.

    Query params:
      - q: free-text query (matches alarm_code, alarm_name, description, steps text)
      - zone: numeric zone (1–22)
      - difficulty: 'Easy' | 'Medium' | 'Hard'
      - page: page number for pagination
    """
    q = request.GET.get("q", "").strip()
    zone = request.GET.get("zone", "").strip()
    diff = request.GET.get("difficulty", "").strip()
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
        ).distinct()

    if zone.isdigit():
        qs = qs.filter(zone=int(zone))

    if diff:
        qs = qs.filter(difficulty=diff)

    paginator = Paginator(qs, 10)  # 10 logs per page
    page_obj = paginator.get_page(page_number)

    context: Dict[str, Any] = {
        "page_obj": page_obj,
        "logs": page_obj.object_list,  # backwards-compat with your template if needed
        "q": q,
        "zone": zone,
        "difficulty": diff,
    }
    return render(request, "maintenance/log_list.html", context)


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


@login_required
@require_http_methods(["GET", "POST"])
def log_create(request: HttpRequest) -> HttpResponse:
    """
    Create a new maintenance log with inline steps (formset).
    Auto-fills zone from equipment if zone is left blank and equipment has a zone.
    """
    if request.method == "POST":
        form = MaintenanceLogForm(request.POST)
        formset = StepFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            log = form.save(commit=False)

            # If zone is blank but equipment has a zone, inherit it.
            if not log.zone and log.equipment and log.equipment.zone:
                log.zone = log.equipment.zone

            log.created_by = request.user
            log.save()

            # Bind the newly saved log to the formset and save steps.
            formset.instance = log
            formset.save()

            messages.success(request, "Maintenance log created successfully.")
            return redirect("maintenance:log_detail", pk=log.pk)
    else:
        form = MaintenanceLogForm()
        formset = StepFormSet()

    return render(request, "maintenance/log_form.html", {"form": form, "formset": formset})


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
