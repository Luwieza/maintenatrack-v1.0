"""Data models for MaintenaTrack.

Contains:
- Equipment: optional asset grouping for logs.
- MaintenanceLog: core log per incident (zone, alarm, LAM, difficulty, etc.).
- Step: ordered steps attached to each log.
"""

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
    asset_tag = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique asset identifier (optional on quick add).",
    )
    zone = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Zone identifier for this equipment (e.g., '1', 'A1', 'Zone-5').",
    )
    location = models.CharField(
        max_length=120, blank=True, help_text="Line/Cell/Bay")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["zone", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "zone"], name="unique_equipment_name_per_zone"
            )
        ]
        indexes = [
            models.Index(fields=["zone", "status"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.asset_tag or 'no-tag'})"


# ---------- MaintenanceLog ----------
class MaintenanceLog(models.Model):
    """A maintenance/repair log entry tied to a zone, alarm, and (optionally) equipment."""

    class Difficulty(models.TextChoices):
        EASY = "Easy", "Easy"
        MEDIUM = "Medium", "Medium"
        HARD = "Hard", "Hard"

    equipment = models.ForeignKey(
        Equipment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="logs",
        help_text="Linked asset, if applicable.",
    )

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="maintenance_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    zone = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Zone identifier where the issue occurred (e.g., '1', 'A1', 'Zone-5').",
    )

    alarm_code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Alarm code - accepts numbers, letters, or mixed (e.g., '123', 'ALM-456', 'A1B2')."
    )
    alarm_name = models.CharField(max_length=150, blank=True)
    lam_checked = models.BooleanField(
        default=False,
        help_text="Line access / lockout or LAM check completed",
    )
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        db_index=True,
    )
    description = models.TextField(
        help_text="Problem statement and high-level approach.",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["zone", "difficulty"]),
            models.Index(fields=["alarm_code"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        equip = str(self.equipment) if self.equipment else f"Zone {self.zone}"
        return f"{equip} | {self.alarm_code} [{self.difficulty}]"

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()

        # Auto-inherit zone from equipment if not provided
        if not self.zone and self.equipment and self.equipment.zone:
            self.zone = self.equipment.zone

        # Validate zone is not empty
        if not self.zone or not str(self.zone).strip():
            raise ValidationError(
                {'zone': 'Zone is required and cannot be empty.'})

        # Validate zone length
        if len(str(self.zone).strip()) > 10:
            raise ValidationError(
                {'zone': 'Zone identifier must be 10 characters or less.'})


# ---------- Step ----------
class Step(models.Model):
    log = models.ForeignKey(
        MaintenanceLog,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    order = models.PositiveSmallIntegerField(
        default=1,
        help_text="Sequence in which the step was performed",
    )
    action = models.TextField(help_text="What was done in this step")
    result = models.TextField(
        blank=True,
        help_text="Observation/result after the action",
    )
    duration_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    performed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="maintenance_steps",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["log", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["log", "order"],
                name="unique_step_order_per_log",
            )
        ]
        indexes = [models.Index(fields=["log", "order"])]

    def __str__(self) -> str:
        return f"Step {self.order} for Log #{self.log_id}"
