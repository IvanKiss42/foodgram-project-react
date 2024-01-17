from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAdminUserOrReadOnly(BasePermission):
    """
    Пермишен, разрешающий только администраторам выполнять действия,
    кроме безопасных методов.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated and request.user.is_admin)


class IsAuthorAdminSuperuserOrReadOnlyPermission(
    permissions.IsAuthenticatedOrReadOnly
):
    """
    Пермишен, позволяющий выполнять безопасные методы для всех пользователей,
    и дополнительно разрешает действия администраторам,
    модераторам и авторам объектов.
    """
    message = (
        'Проверка пользователя является ли он администрацией'
        'или автором объекта, иначе только режим чтения'
    )

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_admin
                or obj.author == request.user)


class IsAdminPermission(BasePermission):
    """
     Пермишен, который разрешает действия
     только аутентифицированным администраторам.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin
