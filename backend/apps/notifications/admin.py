from django.contrib import admin
from django.utils import timezone

from .models import EmailLog, NotificationPreference, SuppressionList


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Read-only: EmailLog is append-only (04.8)."""

    list_display = ("id", "recipient_email", "template_key", "category", "status", "queued_at")
    list_filter = ("status", "category", "sender_role")
    search_fields = ("recipient_email", "template_key", "provider_message_id")
    readonly_fields = [f.name for f in EmailLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SuppressionList)
class SuppressionListAdmin(admin.ModelAdmin):
    list_display = ("email", "reason", "source", "created_at", "released_at")
    list_filter = ("reason", "source")
    search_fields = ("email",)
    actions = ["release_suppression"]

    @admin.action(description="Release selected suppressions (deliberate re-enable)")
    def release_suppression(self, request, queryset):
        queryset.filter(released_at__isnull=True).update(released_at=timezone.now())


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user_id", "category", "is_enabled", "frequency", "changed_at")
    list_filter = ("category", "is_enabled")
