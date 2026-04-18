from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from companies.forms import InternOfferForm
from .models import User, Role, StudentCV
from academics.models import Student, Specialty, Mentor, Department
from .forms import RegisterForm
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from companies.models import Company, Location
from .forms import LoginForm
import random
import string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import Q
from internships.models import Report, Application, Favorite
from internships.models import InternOffer
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from internships.models import InternOffer, Application
import os
from django.core.files.storage import default_storage
from django.conf import settings

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

def home(request):

    context = {
        "total_students": Student.objects.count(),
        "total_companies": Company.objects.count(),
        "total_offers": InternOffer.objects.filter(status="ACTIVE").count(),
        "total_reports": Report.objects.count(),
    }

    return render(request, "home.html", context)


# ================= LOGIN =================

def login_view(request):

    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    form = LoginForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():

            user = form.cleaned_data["user"]

            login(request, user)

            # ако е временна парола
            if user.must_change_password:
                return redirect("change_password")

            return redirect_by_role(user)

        else:
            messages.error(request, "Грешно потребителско име или парола.")

    return render(request, "login.html", {"form": form})

def redirect_by_role(user):

    role = user.role.name

    if role == "STUDENT":
        if hasattr(user, "student"):
            return redirect("student_offers")
        return redirect("login")

    if role == "MENTOR":
        if hasattr(user, "mentor"):
            return redirect("mentor_dashboard")
        return redirect("login")

    if role == "COMPANY":
        return redirect("company_dashboard")

    if role == "SUPER_ADMIN":
        return redirect("/admin/")

    return redirect("login")

# ================= REGISTER =================

def register_view(request):

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data["password"])
            user.save()

            role_name = user.role.name

            # ================= STUDENT =================
            if role_name == "STUDENT":
                Student.objects.create(
                    user=user,
                    faculty_number=form.cleaned_data["faculty_number"],
                    year_of_study=form.cleaned_data["year_of_study"],
                    specialty=form.cleaned_data["specialty"]
                )

            # ================= MENTOR =================
            if role_name == "MENTOR":
                Mentor.objects.create(
                    user=user,
                    department=form.cleaned_data["department"],
                    position=form.cleaned_data["position"]
                )

            # ================= COMPANY =================
            if user.role.name == "COMPANY":
                Company.objects.create(
                    user=user,
                    name=form.cleaned_data["company_name"],
                    contact_person=form.cleaned_data["contact_person"]
                )

            messages.success(request, "Регистрацията е успешна.")
            return redirect("login")

    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


# ================= LOGOUT =================

def logout_view(request):
    logout(request)
    return redirect("home")


# ================= AJAX CHECKS =================

def check_faculty_number(request):
    faculty_number = request.GET.get("faculty_number")
    exists = Student.objects.filter(faculty_number=faculty_number).exists()
    return JsonResponse({"exists": exists})


def check_phone(request):
    phone = request.GET.get("phone")
    exists = User.objects.filter(phone=phone).exists()
    return JsonResponse({"exists": exists})

@require_GET
def check_username(request):
    username = request.GET.get("username", "").strip()

    exists = User.objects.filter(username__iexact=username).exists()

    return JsonResponse({
        "exists": exists
    })


@require_GET
def check_email(request):
    email = request.GET.get("email", "").strip()

    exists = User.objects.filter(email__iexact=email).exists()

    return JsonResponse({
        "exists": exists
    })

def generate_temp_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def password_reset_request(request):

    if request.method == "POST":

        email = request.POST.get("email").strip()

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "Няма потребител с този имейл.")
            return render(request, "password_reset.html")

        # генерираме временна парола
        temp_password = generate_temp_password()

        user.set_password(temp_password)
        user.must_change_password = True
        user.save()

        # изпращаме email
        send_mail(
            "Временна парола - TUniConnect",
            f"""
Здравейте,

Вашата временна парола е:

{temp_password}

Влезте в системата и я сменете веднага.

Поздрави,
TUniConnect
""",
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )

        messages.success(
            request,
            "Изпратихме временна парола на вашия имейл."
        )

        return render(request, "password_reset.html")

    return render(request, "password_reset.html")

@login_required
def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():

            user = form.save()

            user.must_change_password = False
            user.save()

            update_session_auth_hash(request, user)

            messages.success(request, "Паролата е сменена успешно.")

            return redirect_by_role(user)   # 🔥 това е важно

    else:
        form = PasswordChangeForm(request.user)

    return render(request, "change_password.html", {"form": form})

@login_required
def mentor_dashboard(request):

    if request.user.role.name != "MENTOR":
        return redirect("home")

    if not hasattr(request.user, "mentor"):
        return redirect("home")

    mentor = request.user.mentor
    section = request.GET.get("section", "students")

    if request.method == "POST":
        action = request.POST.get("action")
        student_id = request.POST.get("student_id")
        manual_student_name = (request.POST.get("student_name") or "").strip()
        manual_faculty_number = (request.POST.get("faculty_number") or "").strip()

        if action == "assign_student" and student_id:
            student = get_object_or_404(Student, id=student_id)
            student.mentor = mentor
            student.save(update_fields=["mentor"])
            messages.success(request, "Студентът е назначен успешно.")
            return redirect(f"{request.path}?section=assign")

        if action == "assign_student" and manual_student_name:
            candidates = Student.objects.select_related("user")

            if manual_faculty_number:
                candidates = candidates.filter(faculty_number=manual_faculty_number)

            for part in manual_student_name.split():
                candidates = candidates.filter(
                    Q(user__first_name__icontains=part) |
                    Q(user__last_name__icontains=part)
                )

            if candidates.count() == 1:
                student = candidates.first()
                student.mentor = mentor
                student.save(update_fields=["mentor"])
                messages.success(request, "Студентът е назначен успешно (ръчно търсене).")
                return redirect(f"{request.path}?section=assign")

            if candidates.count() == 0:
                messages.error(request, "Не е намерен студент по въведените данни.")
                return redirect(f"{request.path}?section=assign")

            messages.error(
                request,
                "Открити са няколко студента. Добави факултетен номер за точно съвпадение."
            )
            return redirect(f"{request.path}?section=assign")

        if action == "assign_student":
            messages.error(request, "Избери студент от списъка или въведи име ръчно.")
            return redirect(f"{request.path}?section=assign")

        if action == "unassign_student" and student_id:
            student = get_object_or_404(Student, id=student_id, mentor=mentor)
            student.mentor = None
            student.save(update_fields=["mentor"])
            messages.success(request, "Студентът е премахнат от твоите студенти.")
            return redirect(f"{request.path}?section=students")

    students = Student.objects.filter(
        mentor=mentor
    ).select_related("user", "specialty")

    all_students = Student.objects.select_related(
        "user",
        "specialty"
    ).order_by("faculty_number")

    unassigned_or_other_students = all_students.exclude(mentor=mentor)

    applications = Application.objects.filter(
        student__mentor=mentor
    ).select_related(
        "student",
        "student__user",
        "offer",
        "offer__company",
    ).order_by("-submitted_at")

    latest_status_by_student = {}
    for app in applications.order_by("student_id", "-submitted_at"):
        if app.student_id not in latest_status_by_student:
            latest_status_by_student[app.student_id] = app.get_status_display()

    for student in students:
        student.latest_status_display = latest_status_by_student.get(
            student.id,
            "Няма кандидатура"
        )

    workflow_enabled = report_workflow_enabled()

    reports = Report.objects.filter(
        student__mentor=mentor
    ).select_related("student", "student__user")
    if not workflow_enabled:
        reports = reports.only("id", "student_id", "company_id", "report_file", "submitted_at")

    total_students = students.count()
    students_with_internship = students.filter(
        application__status__in=[
            Application.Status.SELECTED,
            Application.Status.SEEN,
        ]
    ).distinct().count()
    students_without_internship = total_students - students_with_internship
    total_reports = reports.count()

    context = {
        "mentor": mentor,
        "section": section,
        "students": students,
        "available_students": unassigned_or_other_students,
        "applications": applications,
        "reports": reports,
        "report_workflow_enabled": workflow_enabled,
        "total_students": total_students,
        "students_with_internship": students_with_internship,
        "students_without_internship": students_without_internship,
        "total_reports": total_reports,
    }

    return render(request, "mentor/dashboard.html", context)

@login_required
def mentor_approve_internship(request, application_id):
    if request.user.role.name != "MENTOR":
        return redirect("home")
    if not hasattr(request.user, "mentor"):
        return redirect("home")

    application = get_object_or_404(
        Application.objects.select_related("student"),
        id=application_id,
        student__mentor=request.user.mentor
    )

    if application.status != Application.Status.SELECTED:
        messages.error(request, "Менторът може да одобрява само избран от студента стаж.")
        return redirect("mentor_dashboard")

    application.status = Application.Status.SEEN
    application.save(update_fields=["status"])
    messages.success(request, "Стажът е одобрен от ментора.")
    return redirect(f"{reverse('mentor_dashboard')}?section=applications")

@login_required
def mentor_approve_report(request, report_id):
    if request.user.role.name != "MENTOR":
        return redirect("home")

    if not report_workflow_enabled():
        messages.error(request, "Липсват миграции за workflow на доклади. Изпълни migrate.")
        return redirect(f"{reverse('mentor_dashboard')}?section=reports")

    mentor = Mentor.objects.filter(user=request.user).first()
    report = get_object_or_404(
        Report.objects.select_related("student"),
        id=report_id,
        student__mentor=mentor
    )

    if report.company_status != Report.ApprovalStatus.APPROVED:
        messages.error(request, "Първо фирмата трябва да одобри доклада.")
        return redirect(f"{reverse('mentor_dashboard')}?section=reports")

    report.mentor_status = Report.ApprovalStatus.APPROVED
    report.save(update_fields=["mentor_status"])
    messages.success(request, "Докладът е одобрен от ментора.")

    return redirect(f"{reverse('mentor_dashboard')}?section=reports")

@login_required
def mentor_applications(request):

    if request.user.role.name != "MENTOR":
        return redirect("home")

    if not hasattr(request.user, "mentor"):
        return redirect("home")

    mentor = request.user.mentor

    applications = Application.objects.filter(
        student__mentor=mentor
    ).select_related(
        "student",
        "student__user",
        "offer"
    )

    return render(request, "mentor/applications.html", {
        "applications": applications
    })

@login_required
def approve_application(request, application_id):

    if request.user.role.name != "MENTOR":
        return redirect("home")

    application = Application.objects.get(id=application_id)

    application.status = Application.Status.APPROVED
    application.save()

    messages.success(request, "Практиката е одобрена.")

    return redirect("mentor_applications")


@login_required
def reject_application(request, application_id):

    if request.user.role.name != "MENTOR":
        return redirect("home")

    application = Application.objects.get(id=application_id)

    application.status = Application.Status.REJECTED
    application.save()

    messages.error(request, "Практиката е отхвърлена.")

    return redirect("mentor_applications")

@login_required
def mentor_offers(request):

    if request.user.role.name != "MENTOR":
        return redirect("home")

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

    paginator = Paginator(offers, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "mentor/offers.html", {
        "offers": page_obj,
        "locations": locations,
        "page_obj": page_obj,
    })

@login_required
def mentor_students_without_internship(request):

    if request.user.role.name != "MENTOR":
        return redirect("home")

    students = Student.objects.select_related(
        "user",
        "specialty"
    )

    student_data = []

    for student in students:

        application = Application.objects.filter(
            student=student
        ).order_by("-submitted_at").first()

        status = "NO_INTERNSHIP"

        if application:

            if application.status == Application.Status.SELECTED:
                status = "INTERNSHIP_SELECTED"

            elif application.status == Application.Status.APPROVED:
                status = "APPROVED_BY_COMPANY"

            elif application.status == Application.Status.WAITING:
                status = "WAITING"

        student_data.append({
            "student": student,
            "status": status
        })

    return render(request, "mentor/students_without_internship.html", {
        "students": student_data
    })

@login_required
def mentor_all_students(request):

    if request.user.role.name != "MENTOR":
        return redirect("home")

    students = Student.objects.select_related(
        "user",
        "specialty",
        "specialty__department"
    )

    return render(request, "mentor/all_students.html", {
        "students": students
    })

@login_required
def company_dashboard(request):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()

    offers = InternOffer.objects.filter(company=company)

    total_offers = offers.count()

    active_offers = offers.filter(
        status=InternOffer.Status.ACTIVE
    ).count()

    applications = Application.objects.filter(
        offer__company=company
    )

    total_applications = applications.count()

    context = {
        "company": company,
        "total_offers": total_offers,
        "active_offers": active_offers,
        "total_applications": total_applications,
        "offers": offers,
    }

    return render(request, "company/dashboard.html", context)

@login_required
def company_offers(request):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()

    offers = InternOffer.objects.filter(company=company).order_by("-created_at")

    return render(request, "company/offers.html", {
        "company": company,
        "offers": offers
    })

@login_required
def company_applications(request):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()
    workflow_enabled = report_workflow_enabled()

    applications = Application.objects.filter(
        offer__company=company
    ).select_related("student", "student__user", "offer").order_by("-submitted_at")

    reports = Report.objects.filter(
        company=company
    ).select_related("student", "student__user").order_by("-submitted_at")
    if not workflow_enabled:
        reports = reports.only("id", "student_id", "company_id", "report_file", "submitted_at")

    reports = Report.objects.filter(
        company=company
    ).select_related("student", "student__user").order_by("-submitted_at")

    return render(request, "company/applications.html", {
        "company": company,
        "applications": applications,
        "reports": reports,
        "report_workflow_enabled": workflow_enabled,
    })

@login_required
def company_approve_report(request, report_id):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()
    report = get_object_or_404(Report, id=report_id, company=company)

    report.company_status = Report.ApprovalStatus.APPROVED
    report.save(update_fields=["company_status"])
    messages.success(request, "Докладът е одобрен от фирмата.")

    return redirect("company_applications")


@login_required
def company_reject_report(request, report_id):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()
    report = get_object_or_404(Report, id=report_id, company=company)

    report.company_status = Report.ApprovalStatus.REJECTED
    report.mentor_status = Report.ApprovalStatus.PENDING
    report.save(update_fields=["company_status", "mentor_status"])
    messages.warning(request, "Докладът е върнат за корекция от фирмата.")

    return redirect("company_applications")

@login_required
def company_application_detail(request, application_id):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()

    application = get_object_or_404(
        Application.objects.select_related("student", "student__user", "offer"),
        id=application_id,
        offer__company=company
    )

    if application.status == Application.Status.WAITING:
        application.status = Application.Status.SEEN
        application.save(update_fields=["status"])

    student_cv = StudentCV.objects.filter(student=application.student).first()
    file_ext = ""
    if application.cv_file:
        file_ext = application.cv_file.name.split(".")[-1].lower()

    cv_text = (application.cv_text or "").strip()
    profile_cv_markers = {
        "кандидатстване с профилно cv",
        "кандидатстване с профилно св",
    }
    has_meaningful_cv_text = bool(
        cv_text and cv_text.lower() not in profile_cv_markers
    )

    if request.method == "POST":
        action = request.POST.get("action")

        student_email = application.student.user.email
        student_name = application.student.user.first_name

        if action == "approve":
            application.status = Application.Status.APPROVED
            application.rejection_reason = ""  # чистим ако има старо
            application.save()

            # ✉️ EMAIL
            send_mail(
                "Промяна в кандидатура - TUniConnect",
                f"""
    Здравей, {student_name},

    Твоята кандидатура за:
    {application.offer.title}

    е ОДОБРЕНА!

    Влез в системата за повече информация.

    Поздрави,
    TUniConnect
    """,
                settings.DEFAULT_FROM_EMAIL,
                [student_email],
            )


        elif action == "reject":
            reason = (request.POST.get("rejection_reason") or "").strip()

            if not reason:
                messages.error(request, "Моля, въведете причина за отказ.")
                return redirect(request.path)

            application.status = Application.Status.REJECTED
            application.rejection_reason = reason
            application.save()

            # ✉️ EMAIL
            send_mail(
                "Промяна в кандидатура - TUniConnect",
                f"""
    Здравей, {student_name},

    Твоята кандидатура за:
    {application.offer.title}

    е ОТХВЪРЛЕНА.

    Причина:
    {reason}

    Можеш да разгледаш други обяви в платформата.

    Поздрави,
    TUniConnect
    """,
                settings.DEFAULT_FROM_EMAIL,
                [student_email],
            )

        return redirect("company_applications")

    return render(request, "company/application_detail.html", {
        "application": application,
        "student_cv": student_cv,
        "cv_file_ext": file_ext,
        "has_meaningful_cv_text": has_meaningful_cv_text,
    })

@login_required
def create_offer(request):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()

    if request.method == "POST":

        form = InternOfferForm(request.POST)

        if form.is_valid():

            offer = form.save(commit=False)
            offer.company = company
            offer.status = InternOffer.Status.DRAFT
            offer.save()

            return redirect("company_offers")

    else:
        form = InternOfferForm()

    return render(request, "company/create_offer.html", {
        "form": form
    })

@login_required
def company_approve_application(request, application_id):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()
    application = get_object_or_404(Application, id=application_id, offer__company=company)

    application.status = Application.Status.APPROVED
    application.save()

    return redirect("company_applications")


@login_required
def company_reject_application(request, application_id):

    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()
    application = get_object_or_404(Application, id=application_id, offer__company=company)

    application.status = Application.Status.REJECTED
    application.save()

    return redirect("company_applications")

@login_required
def apply_for_offer(request, offer_id):

    if request.user.role.name != "STUDENT":
        return redirect("home")

    student = request.user.student
    offer = InternOffer.objects.get(id=offer_id)

    if request.method == "POST":

        cv_type = request.POST.get("cv_type")
        motivation_type = request.POST.get("motivation_type", "text")
        motivation = (request.POST.get("motivation_letter") or "").strip()
        motivation_file = request.FILES.get("motivation_file")

        if motivation_type == "file":
            motivation = ""

        # 🔴 ТУК СЛАГАШ ПРОВЕРКАТА
        if cv_type == "profile":
            cv = StudentCV.objects.filter(student=student).first()

            if not cv or not any([cv.summary, cv.experience, cv.skills, cv.education]):
                messages.error(request, "Нямате попълнено CV.")
                return redirect(request.path)

        # ✅ ако ползва CV от профила
        if cv_type == "profile":
            cv, created = StudentCV.objects.get_or_create(student=student)

            Application.objects.create(
                student=student,
                offer=offer,
                cv_text=(cv.summary or "") + "\n\n" +
                        (cv.experience or "") + "\n\n" +
                        (cv.skills or "") + "\n\n" +
                        (cv.education or ""),
                motivation_letter=motivation,
                motivation_file=motivation_file if motivation_type == "file" else None,
                status=Application.Status.WAITING
            )

        # ✅ ако качва файл
        else:
            file = request.FILES.get("cv_file")

            Application.objects.create(
                student=student,
                offer=offer,
                cv_file=file,
                motivation_letter=motivation,
                motivation_file=motivation_file if motivation_type == "file" else None,
                status=Application.Status.WAITING
            )

        return redirect("student_offers")

    cv = StudentCV.objects.filter(student=student).first()

    has_cv = False
    if cv and any([cv.summary, cv.experience, cv.skills, cv.education]):
        has_cv = True

    return render(request, "student/apply.html", {
        "offer": offer,
        "has_cv": has_cv,
    })

def offer_detail(request, offer_id):

    offer = get_object_or_404(
        InternOffer,
        id=offer_id,
        status=InternOffer.Status.ACTIVE
    )

    has_applied = False
    is_favorite = False

    has_cv = False

    if request.user.is_authenticated and hasattr(request.user, "student"):
        cv = StudentCV.objects.filter(student=request.user.student).first()

        if cv and any([cv.summary, cv.experience, cv.skills, cv.education]):
            has_cv = True

    if request.user.is_authenticated and hasattr(request.user, "student"):
        has_applied = Application.objects.filter(
            student=request.user.student,
            offer=offer
        ).exists()

        is_favorite = Favorite.objects.filter(
            student=request.user.student,
            offer=offer
        ).exists()

    if f"viewed_offer_{offer.id}" not in request.session:
        offer.views += 1
        offer.save(update_fields=["views"])
        request.session[f"viewed_offer_{offer.id}"] = True

    return render(request, "student/offer_detail.html", {
        "offer": offer,
        "has_applied": has_applied,
        "is_favorite": is_favorite,
        "has_cv": has_cv,
    })

from django.core.mail import EmailMessage


def contact_submit(request):
    if request.method == "POST":
        email = request.POST.get("email")
        subject = request.POST.get("subject") or "Ново съобщение от сайта"
        message = request.POST.get("message")

        text_content = f"""
Имейл от: {email}

Съобщение:
{message}
"""

        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding:20px; background:#f4f7fb;">

            <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:12px;">

                <h2 style="color:#0b3d91; margin-bottom:20px;">
                    Ново съобщение от TUniConnect
                </h2>

                <p style="margin:10px 0;">
                    <strong>Имейл от:</strong><br>
                    <a href="mailto:{email}" style="color:#2563eb;">
                        {email}
                    </a>
                </p>

                <p style="margin:10px 0;">
                    <strong>Тема:</strong><br>
                    {subject}
                </p>

                <p style="margin:10px 0;">
                    <strong>Съобщение:</strong>
                </p>

                <div style="
                    background:#f1f5f9;
                    padding:15px;
                    border-radius:8px;
                    line-height:1.5;
                ">
                    {message}
                </div>

                <hr style="margin:25px 0;">

                <p style="font-size:12px; color:#64748b;">
                    Това съобщение е изпратено от контактната форма на TUniConnect.
                </p>

            </div>

        </div>
        """

        email_msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.EMAIL_HOST_USER,
            ["tuniconnect1962@gmail.com"],
            reply_to=[email],
        )

        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

        messages.success(request, "Съобщението е изпратено успешно!")

        return redirect("home")


def about(request):
    return render(request, "about.html")

def edit_offer(request, pk):
    offer = get_object_or_404(InternOffer, pk=pk)

    if request.method == "POST":
        form = InternOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            return redirect("company_offers")  # или как ти се казва страницата
    else:
        form = InternOfferForm(instance=offer)

    return render(request, "company/create_offer.html", {
        "form": form,
        "is_edit": True
    })

@login_required
def quick_apply(request, offer_id):
    offer = get_object_or_404(InternOffer, id=offer_id)
    student = request.user.student

    # ✅ ПРОВЕРКА
    if Application.objects.filter(student=student, offer=offer).exists():
        messages.warning(request, "Вече си кандидатствал по тази обява.")
        return redirect('offer_detail', offer_id=offer.id)

    # ✅ ако НЕ е кандидатствал
    cv, _ = StudentCV.objects.get_or_create(student=student)

    Application.objects.create(
        student=student,
        offer=offer,
        cv_text=(cv.summary or "") + "\n\n" +
                (cv.experience or "") + "\n\n" +
                (cv.skills or "") + "\n\n" +
                (cv.education or ""),
        status=Application.Status.WAITING
    )

    messages.success(request, "Кандидатства успешно 🚀")
    return redirect('offer_detail', offer_id=offer.id)

@login_required
def company_profile(request):
    if request.user.role.name != "COMPANY":
        return redirect("home")

    company = Company.objects.filter(user=request.user).first()
    offers = InternOffer.objects.filter(company=company)

    if request.method == "POST":
        company.description = request.POST.get("description")
        company.history = request.POST.get("history")
        company.career = request.POST.get("career")
        company.employees_count = request.POST.get("employees_count") or None
        company.founded_year = request.POST.get("founded_year") or None


        if request.FILES.get("logo"):
            company.logo = request.FILES["logo"]

        if request.FILES.get("banner"):
            company.banner = request.FILES["banner"]

        company.save()
        return redirect("company_profile")

    return render(request, "company/profile.html", {
        "company": company,
        "offers": offers
    })

def company_public_profile(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    offers = InternOffer.objects.filter(
        company=company,
        status=InternOffer.Status.ACTIVE
    )

    return render(request, "company/public_profile.html", {
        "company": company,
        "offers": offers
    })

    if not report_workflow_enabled():
            messages.error(request, "Липсват миграции за workflow на доклади. Изпълни migrate.")
            return redirect("company_applications")

    if not report_workflow_enabled():
        messages.error(request, "Липсват миграции за workflow на доклади. Изпълни migrate.")
        return redirect("company_applications")