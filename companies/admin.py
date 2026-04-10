from django.contrib import admin
from .models import Company, Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("city_name",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "location")
    search_fields = ("name",)
