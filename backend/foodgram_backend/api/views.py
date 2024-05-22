from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Ingredient, Tag

from .filters import IngredientFilterSet
from .serializers import (IngredientSerializer, TagSerializer,
                          UserAvatarSerializer)

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
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet
