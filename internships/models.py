from django.db import models
from django.core.exceptions import ValidationError
from academics.models import Student, Mentor
from companies.models import Company, Location


class InternOffer(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Чернова"
        ACTIVE = "ACTIVE", "Активна"
        CLOSED = "CLOSED", "Затворена"

    FIELD_CHOICES = [
        ("IT", "ИТ"),
        ("Marketing", "Маркетинг"),
        ("Finance", "Финанси"),
    ]

    SALARY_TYPE_CHOICES = [
        ("Paid", "Платен"),
        ("Unpaid", "Неплатен"),
    ]

    WORKSPACE_TYPE_CHOICES = [
        ("Onsite", "Присъствено"),
        ("Remote", "Дистанционно"),
        ("Hybrid", "Хибридно"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    field = models.CharField(max_length=50, choices=FIELD_CHOICES)
    salary_type = models.CharField(max_length=20, choices=SALARY_TYPE_CHOICES)
    workspace_type = models.CharField(max_length=20, choices=WORKSPACE_TYPE_CHOICES)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    responsibilities = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Обява"
        verbose_name_plural = "Обяви"

    def __str__(self):
        return self.title


class Application(models.Model):

    class Status(models.TextChoices):
        WAITING = "Waiting", "Чакащи.."
        SEEN = "Seen", "Видяно"
        APPROVED = "Approved", "Одобрен"
        REJECTED = "Rejected", "Отхвърлен"
        SELECTED = "Selected", "Избрано от Студент"

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    offer = models.ForeignKey(InternOffer, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )

    # 🔥 FIX ТУК
    cv_file = models.FileField(upload_to="cvs/", null=True, blank=True)
    cv_text = models.TextField(blank=True)

    motivation_letter = models.TextField(blank=True)
    motivation_file = models.FileField(upload_to="motivation_letters/", null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "offer")
        verbose_name = "Кандидатура"
        verbose_name_plural = "Кандидатури"

    def save(self, *args, **kwargs):

        # Вземаме стария статус ако съществува
        if self.pk:
            old_status = Application.objects.get(pk=self.pk).status
        else:
            old_status = None

        # --------------------------------------------------
        # 1️⃣ SELECTED може да стане само ако е било APPROVED
        # --------------------------------------------------
        if self.status == Application.Status.SELECTED:

            if old_status != Application.Status.APPROVED:
                raise ValidationError(
                    "Application can be selected only if it was previously approved."
                )

            # --------------------------------------------------
            # 2️⃣ Само 1 SELECTED на студент
            # --------------------------------------------------
            existing_selected = Application.objects.filter(
                student=self.student,
                status=Application.Status.SELECTED
            ).exclude(pk=self.pk)

            if existing_selected.exists():
                raise ValidationError(
                    "Student can select only one internship."
                )

            # --------------------------------------------------
            # 3️⃣ Всички други APPROVED стават REJECTED
            # --------------------------------------------------
            Application.objects.filter(
                student=self.student,
                status=Application.Status.APPROVED
            ).exclude(pk=self.pk).update(
                status=Application.Status.REJECTED
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} -> {self.offer}"


class Report(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    report_file = models.FileField(upload_to="reports/")
    grade = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Доклад"
        verbose_name_plural = "Доклади"

    def __str__(self):
        return f"Report - {self.student}"

class Favorite(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    offer = models.ForeignKey(InternOffer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "offer")

    def __str__(self):
        return f"{self.student} ❤️ {self.offer}"