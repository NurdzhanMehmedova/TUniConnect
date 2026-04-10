from rest_framework import viewsets
from .models import InternOffer, Application, Report
from .serializers import (
    InternOfferSerializer,
    ApplicationSerializer,
    ReportSerializer
)
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsCompany



class InternOfferViewSet(viewsets.ModelViewSet):
    queryset = InternOffer.objects.all()
    serializer_class = InternOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsCompany()]
        return [IsAuthenticated()]


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    # -------------------------------------------------
    # Кой какво вижда
    # -------------------------------------------------
    def get_queryset(self):
        user = self.request.user

        # STUDENT вижда само своите кандидатури
        if user.role.name == "STUDENT":
            return Application.objects.filter(student__user=user)

        # COMPANY вижда кандидатури към своите обяви
        if user.role.name == "COMPANY":
            return Application.objects.filter(
                offer__company__user=user
            )

        return Application.objects.none()

    # -------------------------------------------------
    # Кой какво може да прави
    # -------------------------------------------------
    def perform_create(self, serializer):
        user = self.request.user

        # Само STUDENT може да създава кандидатура
        if user.role.name != "STUDENT":
            raise PermissionError("Only students can apply.")

        # Връзваме автоматично student-а към user-а
        serializer.save(student=user.student)

    def update(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        # COMPANY може да променя статус
        if user.role.name == "COMPANY":
            return super().update(request, *args, **kwargs)

        # STUDENT може да прави SELECTED
        if user.role.name == "STUDENT":
            if request.data.get("status") == "Selected":
                return super().update(request, *args, **kwargs)

        raise PermissionError("You don't have permission to update this application.")


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    # -------------------------------------------------
    # Кой какво вижда
    # -------------------------------------------------
    def get_queryset(self):
        user = self.request.user

        # STUDENT вижда само своя протокол
        if user.role.name == "STUDENT":
            return Report.objects.filter(student__user=user)

        # MENTOR вижда протоколите на своите студенти
        if user.role.name == "MENTOR":
            return Report.objects.filter(mentor__user=user)

        return Report.objects.none()

    # -------------------------------------------------
    # Кой може да създава
    # -------------------------------------------------
    def perform_create(self, serializer):
        user = self.request.user

        # Само STUDENT качва протокол
        if user.role.name != "STUDENT":
            raise PermissionError("Only students can upload reports.")

        serializer.save(student=user.student)

    # -------------------------------------------------
    # Кой може да update-ва
    # -------------------------------------------------
    def update(self, request, *args, **kwargs):
        user = request.user

        # Само MENTOR може да добавя коментар и оценка
        if user.role.name == "MENTOR":
            return super().update(request, *args, **kwargs)

        raise PermissionError("Only mentor can update report.")
