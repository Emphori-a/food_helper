
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)


class IsAuthorOrAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    """Разрешает доступ только автору объекта, администратору или
    предоставляет доступ только для чтения."""

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS or obj.author == request.user
                or request.user.is_superuser)


class IsOwner(IsAuthenticated):
    """Разрешает доступ только владельцу объекта."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj
