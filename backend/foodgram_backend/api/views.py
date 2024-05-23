from django.contrib.auth import get_user_model
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from shortuuid import uuid

from recipes.models import Ingredient, Recipe, Tag

from .filters import IngredientFilterSet, RecipeFilterSet
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (IngredientSerializer, ReadRecipeSerializer,
                          TagSerializer, UserAvatarSerializer,
                          WriteRecipeSerializer)

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


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in SAFE_METHODS:
            return ReadRecipeSerializer
        return WriteRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['GET'], url_path='get-link')
    def get_link(self, request, pk=None):
        # это работает не так, как я хочу, ссылка не ведет на рецепт,
        # переделать
        recipe = self.get_object()

        if recipe.short_link:
            return Response({'short-link': reverse(
                'api:recipes-detail',
                kwargs={'pk': recipe.pk}) + recipe.short_link},
                status=status.HTTP_200_OK)

        short_link = uuid()
        recipe.short_link = short_link
        recipe.save()

        full_short_link = reverse(
            'api:recipes-detail',
            kwargs={'pk': recipe.pk}) + short_link

        return Response({'short-link': full_short_link},
                        status=status.HTTP_200_OK)
