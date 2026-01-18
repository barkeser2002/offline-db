from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AuditLog, AdSlot

@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    list_filter = ('action',)
    readonly_fields = ('user', 'action', 'details', 'ip_address', 'timestamp')

@admin.register(AdSlot)
class AdSlotAdmin(ModelAdmin):
    list_display = ('name', 'position', 'is_active')
    list_filter = ('position', 'is_active')
