from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import SiteSettings, Blog, SupportTicket, AdSlot

@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    list_display = ('__str__', 'maintenance_mode')

@admin.register(Blog)
class BlogAdmin(ModelAdmin):
    list_display = ('title', 'created_at')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(SupportTicket)
class SupportTicketAdmin(ModelAdmin):
    list_display = ('subject', 'user', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(AdSlot)
class AdSlotAdmin(ModelAdmin):
    list_display = ('position', 'active')
    list_filter = ('active',)
