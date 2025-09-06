# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# ---------- Equipment ----------
class Equipment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        IN_SERVICE = "in_service", "In Service"
        DOWN = "down", "Down"
        RETIRED = "retired", "Retired"

    name = models.CharField(max_length=120, db_index=True)
    asset_tag = models.CharField(max_length=64, unique=True, help_text="Unique asset identifier")
    zone = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(22)],
        db_index=True
    )
    location = models.CharField(max_length=120, blank=True, help_text="Line/Cell/Bay")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["zone", "name"]
        indexes = [
            models.Index(fields=["zone", "status"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.asset_tag})"


# ---------- MaintenanceLog ----------
class MaintenanceLog(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "Easy", "Easy"
        MEDIUM = "Medium", "Medium"
        HARD = "Hard", "Hard"

    equipment = models.ForeignKey(
        Equipment, on_delete=models.PROTECT, related_name="logs"
    )
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="maintenance_logs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Retain zone at log-time in case equipment moves later
    zone = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(22)],
        db_index=True
    )
    alarm_code = models.CharField(max_length=50, db_index=True)
    alarm_name = models.CharField(max_length=150, blank=True)
    lam_checked = models.BooleanField(default=False, help_text="Line access / lockout or LAM check completed")
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, db_index=True)
    description = models.TextField(help_text="Problem statement and high-level approach")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["zone", "difficulty"]),
            models.Index(fields=["alarm_code"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.equipment} | {self.alarm_code} [{self.difficulty}]"


# ---------- Step ----------
class Step(models.Model):
    log = models.ForeignKey(
        MaintenanceLog, on_delete=models.CASCADE, related_name="steps"
    )
    order = models.PositiveSmallIntegerField(default=1, help_text="Sequence in which the step was performed")
    action = models.TextField(help_text="What was done in this step")
    result = models.TextField(blank=True, help_text="Observation/result after the action")
    duration_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    performed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="maintenance_steps"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["log", "order"]
        unique_together = [("log", "order")]  # prevents duplicate sequence numbers per log
        indexes = [models.Index(fields=["log", "order"])]

    def __str__(self):
        return f"Step {self.order} for Log #{self.log_id}"


