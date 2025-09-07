# maintenance/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .models import MaintenanceLog
from .forms import MaintenanceLogForm, StepFormSet
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login

def log_list(request):
    q = request.GET.get("q", "").strip()
    zone = request.GET.get("zone", "").strip()
    diff = request.GET.get("difficulty", "").strip()

    logs = MaintenanceLog.objects.select_related("equipment", "created_by").order_by("-created_at")

    if q:
        logs = logs.filter(
            Q(alarm_code__icontains=q) |
            Q(alarm_name__icontains=q) |
            Q(description__icontains=q) |
            Q(steps__action__icontains=q) |
            Q(steps__result__icontains=q)
        ).distinct()

    if zone.isdigit():
        logs = logs.filter(zone=int(zone))

    if diff:
        logs = logs.filter(difficulty=diff)

    context = {"logs": logs, "q": q, "zone": zone, "difficulty": diff}
    return render(request, "maintenance/log_list.html", context)

def log_detail(request, pk):
    log = get_object_or_404(MaintenanceLog.objects.select_related("equipment", "created_by").prefetch_related("steps"), pk=pk)
    return render(request, "maintenance/log_detail.html", {"log": log})

@login_required
def log_create(request):
    if request.method == "POST":
        form = MaintenanceLogForm(request.POST)
        formset = StepFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            log = form.save(commit=False)
            if not log.zone and log.equipment and log.equipment.zone:
                log.zone = log.equipment.zone
            log.created_by = request.user
            log.save()
            formset.instance = log
            formset.save()
            return redirect("maintenance:log_detail", pk=log.pk)
    else:
        form = MaintenanceLogForm()
        formset = StepFormSet()

    return render(request, "maintenance/log_form.html", {"form": form, "formset": formset})

# Sign-up section.
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("maintenance:log_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
