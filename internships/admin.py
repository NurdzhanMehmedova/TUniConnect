from django.contrib import admin
from .models import InternOffer, Application, Report
from .models import Favorite

@admin.register(InternOffer)
class InternOfferAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "company",
        "field",
        "status",
        "created_at"
    )

    list_filter = ("status", "field")

    actions = ["approve_offers"]

    def approve_offers(self, request, queryset):
        queryset.update(status="ACTIVE")

    approve_offers.short_description = "Одобри избраните обяви"

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("student", "offer", "status", "submitted_at")
    list_filter = ("status",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("student", "company", "grade", "submitted_at")

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("student", "offer", "created_at")