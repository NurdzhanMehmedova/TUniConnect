from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff")
    search_fields = ("username", "email")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
