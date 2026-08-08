from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    # `groups`/`user_permissions` use an explicit `through` model (see
    # accounts/models.py — needed to match the physical `auth_user_groups` /
    # `auth_user_user_permissions` column names). Django's admin.E013 disallows a
    # ManyToManyField with a manually-specified `through` in `filter_horizontal` or
    # `fieldsets`, so both are dropped here. This app doesn't use group-based
    # permissions; is_staff/is_superuser stay editable for the content-seeding workflow.
    filter_horizontal = ()
    fieldsets = tuple(
        (title, {**opts, 'fields': tuple(f for f in opts['fields'] if f not in ('groups', 'user_permissions'))})
        for title, opts in UserAdmin.fieldsets
    )


admin.site.register(CustomUser, CustomUserAdmin)
