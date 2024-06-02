import base64

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
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
from .serializers import (FavoriteCreateSerializer, IngredientSerializer,
                          ReadRecipeSerializer, ShoppingCartCreateSerializer,
                          SubscriptionCreateSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserAvatarSerializer, WriteRecipeSerializer)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями.
    Расширяет стандартный вьюсет из библиотеки djoser.
    """

    pagination_class = LimitOffsetPagination

    @action(detail=False,
            methods=["GET"],
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['PUT', 'PATCH'],
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request, *args, **kwargs):
        """Обновление аватара пользователя."""
        user = request.user
        serializer = UserAvatarSerializer(user, data=request.data,
                                          partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        """Удаление аватара пользователя."""
        user = request.user
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        """Создание подписки на пользователя."""
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        serializer = SubscriptionCreateSerializer(
            data={'following': author.id,
                  'follower': request.user.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, *args, **kwargs):
        """Удаление подписки на пользователя."""
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        delete_subscription, _ = Subscriptions.objects.filter(
            follower=request.user, following=author).delete()
        if not delete_subscription:
            return Response({'errors': 'Такой подписки не существует.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsOwner],
    )
    def subscriptions(self, request, *args, **kwargs):
        """Получение списка подписок пользователя с пагинацией."""
        user = request.user
        followings = User.objects.filter(following__follower=user)
        paginated_followings = self.paginate_queryset(followings)
        serializer = SubscriptionsSerializer(paginated_followings, many=True,
                                             context={
                                                 'request': request
                                             })
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами. Теги доступны только для чтения."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами.
    Ингредиенты доступны только для чтения.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами.
    Права доступа:
        - создание доступно только авторизованным пользователям,
        - редактирование и удаление доступно только автору рецепта,
        - неавторизованному пользователю данные доступны для чтения;
    Фильтрация:
        - по тегам,
        - по автору рецепта,
        - фильтрация рецептов, находящихся в избранном пользователя,
        - фильтрация рецептов, находящихся в списке покупок пользователя.
    Дополнительные возможности:
    - get_link: возвращает короткую ссылку на рецепт:
        - URL: /recipes/{pk}/get-link.
    - shopping_cart: добавляет или удаляет рецепт из списка покупок:
        - URL: /recipes/{pk}/shopping_cart.
    - download_shopping_cart: скачать список покупок в формате txt:
        - URL: /recipes/download_shopping_cart.
    - favorite: добавляет или удаляет рецепт из избранного:
        - URL: /recipes/{pk}/favorite.
    """

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in SAFE_METHODS:
            return ReadRecipeSerializer
        return WriteRecipeSerializer

    @action(detail=True, methods=['GET'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        full_short_link = request.build_absolute_uri(
            reverse('recipe-shortlink',
                    kwargs={'short_link': recipe.short_link})
        )
        return Response({'short-link': full_short_link},
                        status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, *args, **kwargs):
        """Добавляет рецепт в список покупок."""
        serializer = ShoppingCartCreateSerializer(
            data={'user': request.user.id, 'recipe': kwargs.get('pk')},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, *args, **kwargs):
        """Удаляет рецепт из списка покупок."""
        return self.delete_from_list(model=ShoppingCart, user=request.user,
                                     id=kwargs.get('pk'))

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        """Скачать список покупок в формате txt."""
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
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, *args, **kwargs):
        """Добавляет рецепт в избранное."""
        serializer = FavoriteCreateSerializer(
            data={'user': request.user.id, 'recipe': kwargs.get('pk')},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, *args, **kwargs):
        """Удаляет рецепт из избранного."""
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

    def delete_from_list(self, model, user, id):
        """Удаляет рецепт из указанного списка."""
        recipe = get_object_or_404(Recipe, id=id)
        delete_obj, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if not delete_obj:
            return Response({'errors': 'Рецепт уже удален!'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeShortLinkView(APIView):
    """Представление, которое обрабатывает запрос по короткой ссылке.
    Перенаправляет пользователя на детальную страницу рецепта.
    - URL: /s/{short_link}.
    """

    def get(self, request, short_link):
        try:
            recipe_id_bytes = base64.urlsafe_b64decode(
                short_link.encode('utf-8'))
            recipe_id = int(recipe_id_bytes.decode('utf-8'))
            recipe = get_object_or_404(Recipe, id=recipe_id)
            full_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
            return HttpResponseRedirect(full_url)
        except (ValueError, Recipe.DoesNotExist):
            return Response({'error': 'Неверная короткая ссылка.'},
                            status=status.HTTP_400_BAD_REQUEST)
