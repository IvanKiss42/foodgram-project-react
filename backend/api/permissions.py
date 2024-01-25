from rest_framework import permissions


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
