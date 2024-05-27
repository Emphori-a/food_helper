import base64

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Ingredient, Recipe, Tag
from users.models import Subscriptions

from .filters import IngredientFilterSet, RecipeFilterSet
from .permissions import IsAuthorOrAdminOrReadOnly, IsOwner
from .serializers import (IngredientSerializer, ReadRecipeSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserAvatarSerializer, WriteRecipeSerializer)

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

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        if request.method == 'POST':
            serializer = SubscriptionsSerializer(author, data=request.data,
                                                 context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscriptions.objects.create(follower=user, following=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = get_object_or_404(Subscriptions, folower=user,
                                         following=author)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsOwner],
    )
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        followings = User.objects.filter(followers__follower=user)
        print(f"Followings: {followings}")
        paginator = LimitOffsetPagination()
        paginated_followings = paginator.paginate_queryset(followings, request)
        serializer = SubscriptionsSerializer(paginated_followings, many=True,
                                             context={
                                                 'request': request
                                             })
        return paginator.get_paginated_response(serializer.data)


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

        recipe = self.get_object()

        if recipe.short_link:
            short_link = recipe.short_link
        else:
            recipe_id_bytes = str(recipe.id).encode('utf-8')
            short_link = base64.urlsafe_b64encode(
                recipe_id_bytes).decode('utf-8')
            recipe.short_link = short_link
            recipe.save()

        full_short_link = request.build_absolute_uri(
            reverse('recipe-shortlink', kwargs={'short_link': short_link}))
        return Response({'short-link': full_short_link},
                        status=status.HTTP_200_OK)


class RecipeShortLinkView(APIView):
    def get(self, request, short_link):
        try:
            recipe_id_bytes = base64.urlsafe_b64decode(
                short_link.encode('utf-8'))
            recipe_id = int(recipe_id_bytes.decode('utf-8'))
            recipe = get_object_or_404(Recipe, id=recipe_id)
            return redirect('api:recipes-detail', pk=recipe.id)
        except (ValueError, Recipe.DoesNotExist):
            return Response({'error': 'Неверная короткая ссылка.'},
                            status=status.HTTP_400_BAD_REQUEST)
