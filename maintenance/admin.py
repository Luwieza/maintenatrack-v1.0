# Register your models here.
from django.contrib import admin
from .models import Equipment, MaintenanceLog, Step


# ─────────────────────────────────────────────────────────────────────────────
# Inline: Steps inside the Maintenance Log edit page
# ─────────────────────────────────────────────────────────────────────────────
class StepInline(admin.TabularInline):
    model = Step
    extra = 1
    fields = ("order", "action", "result", "duration_minutes", "performed_by")
    autocomplete_fields = ("performed_by",)
    ordering = ("order",)
    show_change_link = True


# ─────────────────────────────────────────────────────────────────────────────
# Equipment Admin
# ─────────────────────────────────────────────────────────────────────────────
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "asset_tag", "zone", "status", "updated_at")
    list_filter = ("status", "zone")
    search_fields = ("name", "asset_tag", "location", "description")
    ordering = ("zone", "name")
    list_per_page = 25


# ─────────────────────────────────────────────────────────────────────────────
# Maintenance Log Admin (with Step inline)
# ─────────────────────────────────────────────────────────────────────────────
@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = (
        "id", "equipment", "zone", "alarm_code", "alarm_name",
        "difficulty", "lam_checked", "created_by", "created_at",
    )
    list_filter = ("difficulty", "lam_checked", "zone", "created_at")
    search_fields = (
        "alarm_code", "alarm_name", "description",
        "equipment__name", "equipment__asset_tag", "created_by__username",
    )
    autocomplete_fields = ("equipment", "created_by")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 25
    inlines = [StepInline]

    def get_queryset(self, request):
        # Reduce N+1 queries in list view
        qs = super().get_queryset(request)
        return qs.select_related("equipment", "created_by")

    # Opinionated: if not provided, assign author and zone defaults
    def save_model(self, request, obj, form, change):
        if obj.created_by_id is None:
            obj.created_by = request.user
        if (obj.zone is None or obj.zone == 0) and obj.equipment and obj.equipment.zone:
            obj.zone = obj.equipment.zone
        super().save_model(request, obj, form, change)

    # Quick action: mark LAM as checked
    @admin.action(description="Mark selected logs as LAM checked")
    def mark_lam_checked(self, request, queryset):
        updated = queryset.update(lam_checked=True)
        self.message_user(request, f"{updated} log(s) marked as LAM checked.")
    actions = ["mark_lam_checked"]


# ─────────────────────────────────────────────────────────────────────────────
# Step Admin (standalone view)
# ─────────────────────────────────────────────────────────────────────────────
@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ("log", "order", "performed_by", "duration_minutes", "created_at")
    list_filter = ("performed_by",)
    search_fields = ("log__alarm_code", "action", "result", "performed_by__username")
    autocomplete_fields = ("log", "performed_by")
    ordering = ("log", "order")

    def save_model(self, request, obj, form, change):
        if obj.performed_by_id is None:
            obj.performed_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────────────────────────────────────
# Optional: brand the admin
# ─────────────────────────────────────────────────────────────────────────────
admin.site.site_header = "MaintenaTrack Admin"
admin.site.site_title = "MaintenaTrack Admin"
admin.site.index_title = "Maintenance Knowledge Base"
