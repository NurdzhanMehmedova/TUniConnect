from django.db.models import Q
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework import viewsets
from internships.models import Favorite
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.contrib import messages
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

def report_workflow_enabled():
    try:
        with connection.cursor() as cursor:
            columns = connection.introspection.get_table_description(
                cursor, Report._meta.db_table
            )
        names = {col.name for col in columns}
        return {"company_status", "mentor_status"}.issubset(names)
    except (OperationalError, ProgrammingError):
        return False


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
    workflow_enabled = report_workflow_enabled()

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

    approved_count = applications.filter(
        status__in=[
            Application.Status.APPROVED,
            Application.Status.SELECTED
        ]
    ).count()
    rejected_count = applications.filter(status=Application.Status.REJECTED).count()
    pending_count = applications.exclude(
        status__in=[
            Application.Status.APPROVED,
            Application.Status.SELECTED,
            Application.Status.REJECTED
        ]
    ).count()

    total_applications = applications.count()
    approved_percentage = (approved_count / total_applications * 100) if total_applications > 0 else 0

    approved_application = applications.filter(
        status=Application.Status.SELECTED
    ).first() or applications.filter(
        status=Application.Status.APPROVED
    ).first()

    report = None
    if approved_application:
        report_qs = Report.objects.filter(student=student).order_by("-submitted_at")
        if not workflow_enabled:
            report_qs = report_qs.only(
                "id", "student_id", "report_file", "grade", "comments", "submitted_at"
            )
        report = report_qs.first()

    context = {
        "student": student,
        "section": section,

        # applications
        "applications": applications,
        "total_applications": total_applications,
        "approved_count": approved_count,
        "approved_percentage": approved_percentage,
        "rejected_count": rejected_count,
        "pending_count": pending_count,

        # progress
        "approved_application": approved_application,
        "report": report,
        "report_workflow_enabled": workflow_enabled,
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
    today = timezone.localdate()

    offers = InternOffer.objects.filter(
        status=InternOffer.Status.ACTIVE
    ).select_related("company", "location")
    if not (
            request.user.is_authenticated
            and getattr(request.user, "role", None)
            and request.user.role.name == "SUPER_ADMIN"
    ):
        offers = offers.filter(end_date__gte=today)

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
    workflow_enabled = report_workflow_enabled()
    reports = Report.objects.filter(student=student).order_by("-submitted_at")
    has_uploaded_report = reports.exists()
    if not workflow_enabled:
        reports = reports.only("id", "student_id", "report_file", "grade", "comments", "submitted_at")
    report_type = request.GET.get("type", "internship")
    valid_report_types = {"employment_contract", "internship"}
    if report_type not in valid_report_types:
        report_type = "internship"

    approved_application = Application.objects.filter(
        student=student,
        status__in=[Application.Status.SELECTED, Application.Status.APPROVED]
    ).select_related("offer", "offer__company").first()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "upload_report":
            if has_uploaded_report:
                messages.error(request, "Вече имаш подаден доклад. Не можеш да качваш втори.")
                return redirect(f"{request.path}?type={report_type}")

            report_file = request.FILES.get("report_file")

            if report_type == "employment_contract" and not approved_application:
                messages.error(request, "Нямате одобрен стаж, за който да подадете отчет.")
                return redirect(f"{request.path}?type={report_type}")

            if not report_file:
                messages.error(request, "Моля, качете файл с отчет.")
                return redirect(f"{request.path}?type={report_type}")

            if report_type == "internship":
                total_hours_raw = (request.POST.get("internship_total_hours") or "").strip()
                try:
                    total_hours = Decimal(total_hours_raw)
                except (InvalidOperation, ValueError):
                    messages.error(request, "Въведи валидни часове в дневника за стажа.")
                    return redirect(f"{request.path}?type={report_type}")

                if total_hours < Decimal("150") or total_hours > Decimal("155"):
                    messages.error(request, "Общият брой часове за стаж към университета трябва да е между 150 и 155.")
                    return redirect(f"{request.path}?type={report_type}")

            Report.objects.create(
                student=student,
                mentor=student.mentor,
                company=approved_application.offer.company if approved_application else None,
                report_file=report_file,
                **(
                    {
                        "company_status": Report.ApprovalStatus.PENDING,
                        "mentor_status": Report.ApprovalStatus.PENDING,
                    }
                    if workflow_enabled
                    else {}
                )
            )
            if workflow_enabled:
                messages.success(request, "Докладът е качен успешно и чака одобрение от фирмата.")
            else:
                messages.warning(request, "Докладът е качен, но е нужна миграция за фирмено/менторско одобрение.")
            return redirect(f"{request.path}?type={report_type}")

    required_hours = 150

    proof_label_map = {
        "employment_contract": "Прикачете трудов договор",
        "internship": "Прикачете служебна бележка, подписана от преподавателя",
    }

    return render(request, "student/reports.html", {
        "reports": reports,
        "approved_application": approved_application,
        "daily_log_rows": range(1, 32),
        "required_hours": required_hours,
        "proof_label": proof_label_map.get(report_type, "Прикачете доказателство"),
        "report_type": report_type,
        "report_workflow_enabled": workflow_enabled,
        "has_uploaded_report": has_uploaded_report,
    })

@login_required
@require_POST
def toggle_favorite(request, offer_id):

    if request.user.role.name != "STUDENT":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    student = request.user.student
    offer = get_object_or_404(
        InternOffer,
        id=offer_id,
        status=InternOffer.Status.ACTIVE,
        end_date__gte=timezone.localdate(),
    )

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
    ).select_related("offer__company", "offer__location").filter(
        offer__status=InternOffer.Status.ACTIVE,
        offer__end_date__gte=timezone.localdate(),
    )

    offers = [f.offer for f in favorites]

    applications = Application.objects.filter(
        student=request.user.student
    ).values_list("offer_id", flat=True)

    return render(request, "student/saved.html", {
        "offers": offers,
        "applied_offers": list(applications)
    })

