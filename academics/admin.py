from django.contrib import admin
from .models import Department, Mentor, MentorStudentRemovalReason, Position, Specialty, Student


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
    search_fields = ("name",)


@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "position")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    list_filter = ("department", "position")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "faculty_number", "specialty", "year_of_study", "mentor")
    list_filter = ("specialty", "year_of_study", "mentor")
    search_fields = ("user__username", "user__first_name", "user__last_name", "faculty_number")


@admin.register(MentorStudentRemovalReason)
class MentorStudentRemovalReasonAdmin(admin.ModelAdmin):
    list_display = ("student", "mentor", "removed_at")
    list_filter = ("removed_at",)
    search_fields = (
        "student__user__username",
        "student__user__first_name",
        "student__user__last_name",
        "mentor__user__username",
    )
    readonly_fields = ("removed_at",)