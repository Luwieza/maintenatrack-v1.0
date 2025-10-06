# maintenance/forms.py
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
        fields = [
            "equipment",
            "zone",
            "alarm_code",
            "alarm_name",
            "lam_checked",
            "difficulty",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ["order", "action", "result", "duration_minutes"]
        widgets = {
            "action": forms.Textarea(attrs={"rows": 2}),
            "result": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields not required for empty forms - they will be filtered out
        self.fields['action'].required = False
        self.fields['order'].required = False

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action', '').strip()
        order = cleaned_data.get('order')

        # If no action provided, clear all fields to make this an empty form
        if not action:
            cleaned_data['action'] = ''
            cleaned_data['result'] = ''
            cleaned_data['order'] = None
            cleaned_data['duration_minutes'] = None
            # Clear any errors for empty forms
            if hasattr(self, '_errors') and self._errors:
                self._errors.clear()
        else:
            # If action is provided, auto-populate order when missing
            if not order:
                prefix_parts = self.prefix.split('-') if self.prefix else []
                try:
                    cleaned_data['order'] = int(prefix_parts[-1]) + 1
                except (ValueError, IndexError, TypeError):
                    cleaned_data['order'] = 1

        return cleaned_data


StepFormSet = inlineformset_factory(
    parent_model=MaintenanceLog,
    model=Step,
    form=StepForm,
    extra=3,          # show 3 blank step slots
    can_delete=False,  # prevent deleting steps inline
    min_num=0,        # minimum number of forms required
    validate_min=False,  # Don't validate minimum - we handle empty forms manually
)
