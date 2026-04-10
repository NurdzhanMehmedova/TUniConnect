from django.urls import path

from . import views
from .views import student_dashboard
from .views import get_specialties
from .views import student_offers
from .views import student_applications
from .views import student_reports
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("get-specialties/", get_specialties, name="get_specialties"),
    path('dashboard/', student_dashboard, name='student_dashboard'),
    path("offers/", student_offers, name="student_offers"),
    path("applications/", student_applications, name="student_applications"),
    path("reports/", student_reports, name="student_reports"),
    path("favorite/<int:offer_id>/", views.toggle_favorite, name="toggle_favorite"),
    path("saved/", views.saved_offers, name="saved_offers"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

def student_root(request):
    return redirect("student_dashboard")