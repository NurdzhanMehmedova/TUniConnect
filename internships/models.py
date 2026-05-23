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
        OFFER = "Offer", "Оферта"
        REJECTED = "Rejected", "Отхвърлен"
        REJECTED_BY_STUDENT = "RejectedByStudent", "Отхвърлено от студента"
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
        old_status = None
        if self.pk:
            old_status = Application.objects.get(pk=self.pk).status

        is_transition_to_selected = (
            self.status == Application.Status.SELECTED
            and old_status != Application.Status.SELECTED
        )

        if is_transition_to_selected:
            if old_status not in [Application.Status.OFFER, Application.Status.APPROVED]:
                raise ValidationError(
                    "Application can be selected only if it was previously approved/offered."
                )

            existing_selected = Application.objects.filter(
                student=self.student,
                status=Application.Status.SELECTED
            ).exclude(pk=self.pk)
            if existing_selected.exists():
                raise ValidationError("Student can select only one internship.")

        super().save(*args, **kwargs)

        if is_transition_to_selected:
            Application.objects.filter(
                student=self.student,
                status__in=[Application.Status.OFFER, Application.Status.APPROVED],
            ).exclude(pk=self.pk).update(
                status=Application.Status.REJECTED_BY_STUDENT
            )

    def __str__(self):
        return f"{self.student} -> {self.offer}"

class Report(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Чака одобрение"
        APPROVED = "APPROVED", "Одобрен"
        REJECTED = "REJECTED", "Върнат за корекция"
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    report_file = models.FileField(upload_to="reports/")
    grade = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    company_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )
    mentor_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    report_type = models.CharField(max_length=50, blank=True)

    mentor_full_name = models.CharField(max_length=255, blank=True)
    mentor_department = models.CharField(max_length=255, blank=True)

    internship_track = models.CharField(max_length=255, blank=True)

    internship_from = models.DateField(null=True, blank=True)
    internship_to = models.DateField(null=True, blank=True)

    internship_goals = models.TextField(blank=True)

    company_eik = models.CharField(max_length=50, blank=True)

    employment_start_date = models.DateField(null=True, blank=True)
    employment_end_date = models.DateField(null=True, blank=True)

    employment_description = models.TextField(blank=True)

    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    internship_total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Доклад"
        verbose_name_plural = "Доклади"

    def __str__(self):
        return f"Report - {self.student}"

class InternshipDailyLog(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Чернова"
        SUBMITTED = "SUBMITTED", "Изпратен"

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=1)
    task = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.student} - {self.date}"

class Favorite(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    offer = models.ForeignKey(InternOffer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "offer")

    def __str__(self):
        return f"{self.student} ❤️ {self.offer}"