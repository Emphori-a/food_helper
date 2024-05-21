from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import UserAvatarSerializer

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями.
    Расширяет стандартный вьюсет из библиотеки djoser:
        - добавлена возможность добавления и удаления аватара."""
    pagination_class = LimitOffsetPagination

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['PUT', 'PATCH', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request, *args, **kwargs):
        user = request.user
        if request.method in ('PATCH', 'PUT'):
            serializer = UserAvatarSerializer(user, data=request.data,
                                              partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        # elif request.method == 'DELETE':
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
