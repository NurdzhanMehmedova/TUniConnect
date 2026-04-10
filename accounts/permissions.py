from rest_framework.permissions import BasePermission


def has_role(user, role_name):
    return (
        user.is_authenticated and
        user.role and
        user.role.name == role_name
    )


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, "SUPER_ADMIN")


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, "ADMIN")


class IsCompany(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, "COMPANY")


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, "STUDENT")


class IsMentor(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, "MENTOR")
