from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from core.constans import ADMIN_LIST_PER_PAGE

from .models import Subscriptions

User = get_user_model()
admin.site.empty_value_display = 'Не задано'


class FollowerInline(admin.StackedInline):
    model = Subscriptions
    fk_name = 'follower'
    extra = 0
    verbose_name = 'Подписчик'
    verbose_name_plural = 'Подписчики'


class FollowingInline(admin.StackedInline):
    model = Subscriptions
    fk_name = 'following'
    extra = 0
    verbose_name = 'Подписка'
    verbose_name_plural = 'Подписки'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (FollowerInline, FollowingInline)
    fieldsets = UserAdmin.fieldsets + (
        ('Extra fields', {'fields': ('avatar',)}),
    )


@admin.register(Subscriptions)
class Subscriptions(admin.ModelAdmin):
    list_display = ('follower', 'following')
    list_per_page = ADMIN_LIST_PER_PAGE
    list_display_links = ('follower',)
    search_fields = ('following',)
    list_filter = ('follower',)
