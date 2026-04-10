from django.db import models
from accounts.models import User


class Department(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Катедра"
        verbose_name_plural = "Катедри"

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Длъжност"
        verbose_name_plural = "Длъжности"

    def __str__(self):
        return self.name


class Specialty(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="specialties"
    )

    class Meta:
        verbose_name = "Специалност"
        verbose_name_plural = "Специалности"

    def __str__(self):
        return f"{self.name} ({self.department.name})"

class Mentor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Ментор"
        verbose_name_plural = "Ментори"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    faculty_number = models.CharField(max_length=8, unique=True)
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True)
    year_of_study = models.IntegerField()
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенти"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
