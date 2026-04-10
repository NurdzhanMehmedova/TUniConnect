from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from rest_framework import viewsets
from internships.models import Favorite
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from companies.models import Location
from accounts.models import StudentCV
from academics.models import (
    Student,
    Mentor,
    Department,
    Position,
    Specialty,
)

from .serializers import (
    StudentSerializer,
    MentorSerializer,
    DepartmentSerializer,
    PositionSerializer,
    SpecialtySerializer,
)

from internships.models import Application, Report, InternOffer


# ============================
# API VIEWSETS
# ============================

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class MentorViewSet(viewsets.ModelViewSet):
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer


# ============================
# STUDENT DASHBOARD
# ============================

@login_required
def student_dashboard(request):
    if request.user.role.name != "STUDENT":
        return redirect("login")

    if not hasattr(request.user, "student"):
        return redirect("login")

    student = request.user.student
    section = request.GET.get("section", "data")
    cv, created = StudentCV.objects.get_or_create(student=student)

    if request.method == "POST":

        action = request.POST.get("action")

        # 📸 UPLOAD СНИМКА
        if action == "upload_photo":
            if request.FILES.get("profile_image"):
                request.user.profile_image = request.FILES["profile_image"]
                request.user.save()
            return redirect(f"{request.path}?section=cv")

        # 📝 SAVE CV
        if action == "save_cv":
            cv.summary = request.POST.get("summary") or ""
            cv.skills = request.POST.get("skills") or ""
            cv.experience = request.POST.get("experience") or ""
            cv.education = request.POST.get("education") or ""
            cv.save()

            return redirect(f"{request.path}?section=cv")

    applications = Application.objects.filter(student=student).select_related("offer")

    approved_count = applications.filter(status=Application.Status.APPROVED).count()
    rejected_count = applications.filter(status=Application.Status.REJECTED).count()
    pending_count = applications.exclude(
        status__in=[
            Application.Status.APPROVED,
            Application.Status.REJECTED
        ]
    ).count()

    total_applications = applications.count()

    approved_application = applications.filter(
        status=Application.Status.APPROVED
    ).first()

    report = None
    if approved_application:
        report = Report.objects.filter(student=student).first()

    context = {
        "student": student,
        "section": section,

        # applications
        "applications": applications,
        "total_applications": total_applications,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "pending_count": pending_count,

        # progress
        "approved_application": approved_application,
        "report": report,
        "cv": cv,
    }

    return render(request, "student/dashboard.html", context)

# ============================
# AJAX – Dynamic Specialties
# ============================

def get_specialties(request):
    department_id = request.GET.get("department_id")

    if not department_id:
        return JsonResponse([], safe=False)

    specialties = Specialty.objects.filter(department_id=department_id)

    data = [
        {
            "id": s.id,
            "name": s.name
        }
        for s in specialties
    ]

    return JsonResponse(data, safe=False)


# ============================
# STUDENT OFFERS
# ============================


def student_offers(request):

    offers = InternOffer.objects.filter(
        status=InternOffer.Status.ACTIVE
    ).select_related("company", "location")

    search = request.GET.get("search")
    field = request.GET.get("field")
    workspace = request.GET.get("workspace")
    salary = request.GET.get("salary")
    location = request.GET.get("location")

    if field:
        offers = offers.filter(field=field)

    if workspace:
        offers = offers.filter(workspace_type=workspace)

    if salary:
        offers = offers.filter(salary_type=salary)

    if location:
        offers = offers.filter(location_id=location)

    if search:
        offers = offers.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(company__name__icontains=search)
        )

    locations = Location.objects.all()

    # 🔥 FAVORITES (ПРАВИЛНО МЯСТО)
    favorites = []

    if request.user.is_authenticated and hasattr(request.user, "student"):
        favorites = Favorite.objects.filter(
            student=request.user.student
        ).values_list("offer_id", flat=True)

    applications = []

    if request.user.is_authenticated and hasattr(request.user, "student"):
        applications = Application.objects.filter(
            student=request.user.student
        ).values_list("offer_id", flat=True)

    # 🔥 PAGINATION
    paginator = Paginator(offers, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "offers": page_obj,
        "locations": locations,
        "page_obj": page_obj,
        "favorites": list(favorites),  # ✅ ТОВА ЛИПСВАШЕ
        "applied_offers": list(applications),
    }

    return render(request, "student/offers.html", context)


# ============================
# STUDENT APPLICATIONS
# ============================

@login_required
def student_applications(request):

    if not hasattr(request.user, "student") or request.user.role.name != "STUDENT":
        return redirect("home")

    student = request.user.student
    applications = Application.objects.filter(student=student)

    return render(request, "student/applications.html", {
        "applications": applications
    })


# ============================
# STUDENT REPORTS
# ============================

@login_required
def student_reports(request):

    if not hasattr(request.user, "student") or request.user.role.name != "STUDENT":
        return redirect("home")

    student = request.user.student
    reports = Report.objects.filter(student=student)

    return render(request, "student/reports.html", {
        "reports": reports
    })

@login_required
@require_POST
def toggle_favorite(request, offer_id):

    if request.user.role.name != "STUDENT":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    student = request.user.student
    offer = InternOffer.objects.get(id=offer_id)

    favorite, created = Favorite.objects.get_or_create(
        student=student,
        offer=offer
    )

    if not created:
        favorite.delete()
        return JsonResponse({"saved": False})

    return JsonResponse({"saved": True})

@login_required
def saved_offers(request):

    if request.user.role.name != "STUDENT":
        return redirect("home")

    student = request.user.student

    favorites = Favorite.objects.filter(
        student=student
    ).select_related("offer__company", "offer__location")

    offers = [f.offer for f in favorites]

    applications = Application.objects.filter(
        student=request.user.student
    ).values_list("offer_id", flat=True)

    return render(request, "student/saved.html", {
        "offers": offers,
        "applied_offers": list(applications)
    })

