from django import forms
from django.forms import inlineformset_factory
from .models import MaintenanceLog, Step, Equipment


class EquipmentForm(forms.ModelForm):
    """Form for adding new equipment (used by modal / AJAX or a separate view)."""

    class Meta:
        model = Equipment
        fields = ["name", "asset_tag", "zone",
                  "location", "status", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = ["equipment", "zone", "alarm_code", "alarm_name",
                  "lam_checked", "difficulty", "description"]


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
