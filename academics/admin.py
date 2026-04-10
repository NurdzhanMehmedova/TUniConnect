from django.contrib import admin
from .models import Department, Position, Specialty, Mentor, Student


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "department")
    list_filter = ("department",)
    search_fields = ("name",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "position")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "faculty_number", "specialty", "year_of_study")
    list_filter = ("specialty", "year_of_study")