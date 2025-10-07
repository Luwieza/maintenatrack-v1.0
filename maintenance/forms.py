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

    def clean_alarm_code(self):
        """Sanitize alarm code input"""
        alarm_code = self.cleaned_data.get('alarm_code', '').strip()
        if not alarm_code:
            raise forms.ValidationError("Alarm code is required.")
        # Remove potentially harmful characters
        import re
        alarm_code = re.sub(r'[^\w\-\_\.]', '', alarm_code)
        if len(alarm_code) > 50:
            raise forms.ValidationError(
                "Alarm code must be 50 characters or less.")
        return alarm_code.upper()

    def clean_zone(self):
        """Validate zone is within allowed range"""
        zone = self.cleaned_data.get('zone')
        if zone is not None and (zone < 1 or zone > 22):
            raise forms.ValidationError("Zone must be between 1 and 22.")
        return zone


class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ["order", "action", "result", "duration_minutes"]

    def clean_action(self):
        """Sanitize action input"""
        action = self.cleaned_data.get('action', '').strip()
        if action and len(action) > 1000:
            raise forms.ValidationError(
                "Action description must be 1000 characters or less.")
        return action

    def clean_result(self):
        """Sanitize result input"""
        result = self.cleaned_data.get('result', '').strip()
        if result and len(result) > 1000:
            raise forms.ValidationError(
                "Result description must be 1000 characters or less.")
        return result

    def clean_duration_minutes(self):
        """Validate duration is reasonable"""
        duration = self.cleaned_data.get('duration_minutes')
        if duration is not None and (duration < 0 or duration > 1440):  # Max 24 hours
            raise forms.ValidationError(
                "Duration must be between 0 and 1440 minutes (24 hours).")
        return duration


StepFormSet = inlineformset_factory(
    parent_model=MaintenanceLog,
    model=Step,
    form=StepForm,
    extra=3,              # you can tune this
    can_delete=False
)
