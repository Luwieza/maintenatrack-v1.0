# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class MaintenanceLog(models.Model):
    ZONES = [(i, f"Zone {i}") for i in range(1, 23)]
    LEVELS = [("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")]

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    zone = models.IntegerField(choices=ZONES)
    alarm_code = models.CharField(max_length=50)
    alarm_name = models.CharField(max_length=150, blank=True)
    lam_checked = models.BooleanField(default=False)
    difficulty = models.CharField(max_length=10, choices=LEVELS)
    description = models.TextField(help_text="Steps taken to fix the problem.")

    def __str__(self):
        return f"[Zone {self.zone}] {self.alarm_code} ({self.difficulty})"

