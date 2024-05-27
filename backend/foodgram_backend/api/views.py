import base64

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Favorite, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscriptions

from .filters import IngredientFilterSet, RecipeFilterSet
from .permissions import IsAuthorOrAdminOrReadOnly, IsOwner
from .serializers import (IngredientSerializer, ReadRecipeSerializer,
                          ShortRecipesSerializer, SubscriptionsSerializer,
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

        subscription = Subscriptions.objects.filter(
            follower=user, following__id=self.kwargs.get('id'))
        if not subscription.exists():
            raise ValidationError('Такой подписки не существует.')
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

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.add_to_list(model=ShoppingCart, user=request.user,
                                    id=kwargs.get('pk'))
        return self.delete_from_list(model=ShoppingCart, user=request.user,
                                     id=kwargs.get('pk'))

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        user = request.user
        shopping_cart = user.shopping_cart.select_related('recipe').all()
        if not shopping_cart:
            raise ValidationError('Ваш список покупок пуст.')

        ingredients = IngredientInRecipe.objects.filter(
            recipe__in=[item.recipe for item in shopping_cart]
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = self.generate_shopping_list(ingredients)

        response = HttpResponse(shopping_list, content_type='text/plain')
        filename = f'{user.username}_shopping_list.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.add_to_list(model=Favorite, user=request.user,
                                    id=kwargs.get('pk'))
        return self.delete_from_list(model=Favorite, user=request.user,
                                     id=kwargs.get('pk'))

    def generate_shopping_list(self, ingredients):
        """
        Генерирует текстовый список покупок из переданных ингредиентов.

        Аргументы:
            ingredients: QuerySet с аннотированными данными ингредиентов.
        Возвращает:
            строка с текстовым списком покупок.
        """
        shopping_list = []
        for item in ingredients:
            shopping_list.append(
                (f'{item["ingredient__name"]} '
                 f'({item["ingredient__measurement_unit"]}) — '
                 f'{item["total_amount"]}')
            )
        return "\n".join(shopping_list)

    def add_to_list(self, model, user, id):
        if model.objects.filter(user=user, recipe__id=id).exists():
            raise ValidationError(f'Рецепт с id {id} уже добавлен в {model}')
        try:
            recipe = get_object_or_404(Recipe, id=id)
        except Http404:
            raise ValidationError(
                'Такого рецепта не существует.')
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipesSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from_list(self, model, user, id):
        obj = model.objects.filter(user=user, recipe__id=id)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        get_object_or_404(Recipe, id=id)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_400_BAD_REQUEST)


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
