from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts import views_frontend
from academics.views import get_specialties
from django.conf import settings
from django.conf.urls.static import static

# ================= API VIEWSETS =================

from internships.views import (
    InternOfferViewSet,
    ApplicationViewSet,
    ReportViewSet,
)

from academics.views import (
    StudentViewSet,
    MentorViewSet,
    DepartmentViewSet,
    PositionViewSet,
    SpecialtyViewSet,
)

from companies.views import (
    CompanyViewSet,
    LocationViewSet,
)

from accounts.views import (
    UserViewSet,
    RoleViewSet,
)

from accounts.views_frontend import (
    mentor_dashboard,
    mentor_applications,
    approve_application,
    reject_application, company_dashboard, company_offers, edit_offer, create_offer, company_applications,
    company_application_detail,
    company_approve_application,
    company_reject_application, quick_apply, mentor_approve_internship
)

# ================= FRONTEND =================

from accounts.views_frontend import (
    home,
    login_view,
    register_view,
    logout_view, check_faculty_number, check_username, check_email, mentor_dashboard,
)

# ================= JWT =================

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()

# Internships
router.register(r'offers', InternOfferViewSet)
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'reports', ReportViewSet, basename='report')

# Companies
router.register(r'companies', CompanyViewSet)
router.register(r'locations', LocationViewSet)

# Academics
router.register(r'students', StudentViewSet)
router.register(r'mentors', MentorViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'positions', PositionViewSet)
router.register(r'specialties', SpecialtyViewSet)

# Accounts
router.register(r'users', UserViewSet)
router.register(r'roles', RoleViewSet)

urlpatterns = [

    # Admin
    path('admin/', admin.site.urls),

    # ================= API =================
    path('api/', include(router.urls)),

    # JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ================= FRONTEND =================
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path("check-fn/", views_frontend.check_faculty_number, name="check_fn"),
    path("check-username/", check_username, name="check_username"),
    path("check-email/", check_email, name="check_email"),
    path("ajax/check-username/", views_frontend.check_username, name="check_username"),
    path("ajax/check-email/", views_frontend.check_email, name="check_email"),
    path("ajax/check-phone/", views_frontend.check_phone, name="check_phone"),
    path("ajax/get-specialties/", get_specialties, name="get_specialties"),
    path("mentor/dashboard/", mentor_dashboard, name="mentor_dashboard"),
    path("mentor/applications/", mentor_applications, name="mentor_applications"),
    path("mentor/applications/<int:application_id>/approve/", approve_application, name="approve_application"),
    path("mentor/applications/<int:application_id>/reject/", reject_application, name="reject_application"),
    path("mentor/applications/<int:application_id>/approve-internship/", mentor_approve_internship, name="mentor_approve_internship"),
    path("mentor/offers/", views_frontend.mentor_offers, name="mentor_offers"),
    path("mentor/all-students/", views_frontend.mentor_all_students, name="mentor_all_students"),
    path("mentor/students-no-internship/", views_frontend.mentor_students_without_internship, name="mentor_students_without_internship"),
    path("dashboard/", company_dashboard, name="company_dashboard"),
    path("offers/", company_offers, name="company_offers"),
    path("offers/create/", create_offer, name="create_offer"),
    path("applications/",company_applications,name="company_applications"),
    path("applications/<int:application_id>/", company_application_detail, name="company_application_detail"),
    path("contact-submit/", views_frontend.contact_submit, name="contact_submit"),
    path("about/", views_frontend.about, name="about"),
    path("company/application/<int:application_id>/approve/",company_approve_application,name="company_approve_application"),
    path("company/application/<int:application_id>/reject/",company_reject_application,name="company_reject_application"),
    path("offers/<int:offer_id>/apply/",views_frontend.apply_for_offer,name="apply_for_offer"),
    path('offer/<int:pk>/edit/', views_frontend.edit_offer, name='edit_offer'),
    path('offers/<int:offer_id>/quick-apply/', quick_apply, name='quick_apply'),

    # Password Reset (временна парола)
    path("change-password/",views_frontend.change_password,name="change_password"),

    path("offers/<int:offer_id>/",views_frontend.offer_detail,name="offer_detail"),

    # ACADEMICS FRONTEND
    path('student/', include('academics.urls')),
    path("password-reset/",views_frontend.password_reset_request,name="password_reset"),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)