from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class Role(models.Model):
    ROLE_CHOICES = {
        "STUDENT": "Студент",
        "MENTOR": "Ментор",
        "COMPANY": "Компания",
        "SUPER_ADMIN": "Администратор"
    }

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Роля"
        verbose_name_plural = "Роли"

    def display_name(self):
        return self.ROLE_CHOICES.get(self.name, self.name)

    def __str__(self):
        return self.name


class User(AbstractUser):
    phone = models.CharField(max_length=20, unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    must_change_password = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to="profiles/",null=True,blank=True)

    class Meta:
        verbose_name = "Потребител"
        verbose_name_plural = "Потребители"

    def __str__(self):
        return self.username


@receiver(post_save, sender=User)
def assign_super_admin_role(sender, instance, created, **kwargs):
    if instance.is_superuser:
        try:
            super_admin_role = Role.objects.get(name="SUPER_ADMIN")
            if instance.role != super_admin_role:
                instance.role = super_admin_role
                instance.save()
        except Role.DoesNotExist:
            pass

class StudentCV(models.Model):
    student = models.OneToOneField("academics.Student", on_delete=models.CASCADE)

    summary = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CV of {self.student.user.username}"