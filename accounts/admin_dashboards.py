from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from companies.models import Company
from internships.models import Application, InternOffer


@staff_member_required
def admin_overview_dashboard(request):
    app_status = list(
        Application.objects.values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    offer_status = list(
        InternOffer.objects.values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    role_counts = list(
        User.objects.values("role__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    context = {
        "title": "Оперативен дашборд",
        "total_users": User.objects.count(),
        "total_companies": Company.objects.count(),
        "total_offers": InternOffer.objects.count(),
        "total_applications": Application.objects.count(),
        "app_status": app_status,
        "offer_status": offer_status,
        "role_counts": role_counts,
        "app_status_labels": [r["status"] for r in app_status],
        "app_status_values": [r["total"] for r in app_status],
        "offer_status_labels": [r["status"] for r in offer_status],
        "offer_status_values": [r["total"] for r in offer_status],
        "role_labels": [r["role__name"] or "Без роля" for r in role_counts],
        "role_values": [r["total"] for r in role_counts],
    }
    return render(request, "admin/custom_dashboard_overview.html", context)


@staff_member_required
def admin_quality_dashboard(request):
    latest_applications = Application.objects.select_related("student__user", "offer").order_by("-submitted_at")[:12]
    latest_offers = InternOffer.objects.select_related("company").order_by("-created_at")[:12]

    since = timezone.now() - timedelta(days=14)

    app_daily_raw = (
        Application.objects.filter(submitted_at__gte=since)
        .annotate(day=TruncDate("submitted_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    offer_daily_raw = (
        InternOffer.objects.filter(created_at__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    app_map = {r["day"]: r["total"] for r in app_daily_raw}
    offer_map = {r["day"]: r["total"] for r in offer_daily_raw}

    day_labels = []
    app_daily_values = []
    offer_daily_values = []
    for offset in range(14):
        day = (since + timedelta(days=offset)).date()
        day_labels.append(day.strftime("%d.%m"))
        app_daily_values.append(app_map.get(day, 0))
        offer_daily_values.append(offer_map.get(day, 0))

    context = {
        "title": "Дашборд за активност",
        "latest_applications": latest_applications,
        "latest_offers": latest_offers,
        "day_labels": day_labels,
        "app_daily_values": app_daily_values,
        "offer_daily_values": offer_daily_values,
    }
    return render(request, "admin/custom_dashboard_quality.html", context)