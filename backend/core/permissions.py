from rest_framework import permissions

def check_is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, 'profile', None)
    return profile is not None and profile.role == 'admin'

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access for operators and guests,
    while restricting write/mutate actions strictly to administrators.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return check_is_admin(request.user)

class IsAdminUserOnly(permissions.BasePermission):
    """Restricts access exclusively to administrators."""
    def has_permission(self, request, view):
        return check_is_admin(request.user)
