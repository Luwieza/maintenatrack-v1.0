# maintenance/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import MaintenanceLog, Step

class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = ["equipment", "zone", "alarm_code", "alarm_name", "lam_checked", "difficulty", "description"]

class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ["order", "action", "result", "duration_minutes"]

StepFormSet = inlineformset_factory(
    parent_model=MaintenanceLog,
    model=Step,
    form=StepForm,
    extra=3,              # you can tune this
    can_delete=False
)
