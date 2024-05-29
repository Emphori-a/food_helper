
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        BasePermission, )


class CurrentUserOrAdminOrReadOnly(BasePermission):
    """Разрешает доступ только текущему пользователю, администратору
    или предоставляет доступ только для чтения."""

    def has_permission(self, request, view):
        if view.action == 'retrieve' and view.detail:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user or request.user.is_staff


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """Разрешает доступ только автору объекта, администратору или
    предоставляет доступ только для чтения."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return (obj.author == request.user
                or request.user.is_superuser)


class IsOwner(IsAuthenticated):
    """Разрешает доступ только владельцу объекта."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj
