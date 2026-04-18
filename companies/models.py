from django.db import models
from accounts.models import User


class Location(models.Model):

    CITY_CHOICES = {
        "Sofia": "София",
        "Plovdiv": "Пловдив",
        "Varna": "Варна",
        "Burgas": "Бургас",
        "Ruse": "Русе",
        "Stara Zagora": "Стара Загора",
        "Pleven": "Плевен",
    }

    city_name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Локация"
        verbose_name_plural = "Локации"

    def display_name(self):
        return self.CITY_CHOICES.get(self.city_name, self.city_name)

    def __str__(self):
        return self.city_name


class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=255)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    banner = models.ImageField(upload_to="company_banners/", blank=True, null=True)
    employees_count = models.IntegerField(blank=True, null=True)
    founded_year = models.IntegerField(blank=True, null=True)
    history = models.TextField(blank=True, null=True)
    career = models.TextField(blank=True, null=True)

    @property
    def image_url(self):
        if self.logo:
            return self.logo.url
        return "/static/images/logo_placeholder.png"

    @property
    def banner_url(self):
        if self.banner:
            return self.banner.url
        return "/static/images/default-banner.png"

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return self.name
