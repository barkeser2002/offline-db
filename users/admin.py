from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from .models import User, Wallet, WatchLog

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('is_premium',)}),
    )
    list_display = ('username', 'email', 'is_staff', 'is_premium')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'is_premium')

@admin.register(Wallet)
class WalletAdmin(ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)

@admin.register(WatchLog)
class WatchLogAdmin(ModelAdmin):
    list_display = ('user', 'episode', 'duration', 'watched_at')
    list_filter = ('watched_at',)
    search_fields = ('user__username', 'episode__title')
