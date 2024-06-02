from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from recipes.models import (Favorite, Ingredient, IngredientInRecipe,
                            ShoppingCart, Recipe, Tag)
from users.models import Subscriptions

User = get_user_model()


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        """Проверяет наличие аватара в данных.
        Аргументы: data - данные для проверки.
        Возвращает: валидированные данные.
        Ошибки валидации: если поле avatar отсутствует или равно None.
        """
        if 'avatar' not in data or data['avatar'] is None:
            raise serializers.ValidationError(
                {"avatar": "Это поле обязательно."})
        return data


class CustomUserSerializer(UserSerializer):
    """Кастомный сериализатор для пользователя, добавляет поле is_subscribed.
    """

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного пользователя.
        Аргументы: obj - объект пользователя.
        Возвращает: True если подписан, иначе False.
        """
        request = self.context.get('request', None)
        return bool(request and request.user.is_authenticated
                    and Subscriptions.objects.filter(
                        follower=request.user, following=obj).exists())


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для представления списка ингридиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(source='ingredients_in',
                                               many=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в списке покупок пользователя.
        Аргументы: obj - объект рецепта.
        Возвращает: True если в списке покупок, иначе False.
        """
        request = self.context.get('request', None)
        return bool(request and request.user.is_authenticated
                    and ShoppingCart.objects.filter(
                        user=request.user, recipe=obj).exists())

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном пользователя.
        Аргументы: obj - объект рецепта.
        Возвращает: True если в избранном, иначе False.
        """
        request = self.context.get('request', None)
        return bool(request and request.user.is_authenticated
                    and Favorite.objects.filter(
                        user=request.user, recipe=obj).exists())


class WriteIngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class WriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
    )
    image = Base64ImageField()
    ingredients = WriteIngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time', 'author')

    def validate(self, data):
        """Выполняет валидацию тегов и ингредиентов.
        Аргументы: data - данные для проверки.
        Возвращает: валидированные данные.
        Ошибки валидации:
            - если поля tags или ingredients пустые,
            - если поля tags или ingredients содержат дубликаты.
        """
        tags = data.get('tags')
        if not tags:
            raise ValidationError('Поле тегов не может быть пустым.')
        if len(tags) != len(set(tags)):
            raise ValidationError('Теги не должны повторяться.')

        ingredients = data.get('ingredients')
        if not ingredients:
            raise ValidationError('Поле ингредиентов не может быть пустым.')
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if (len(tags) != len(set(tags))
                or len(ingredient_ids) != len(set(ingredient_ids))):
            raise ValidationError('Ингредиенты не должны повторяться.')

        return data

    def validate_image(self, data):
        """Проверяет наличие изображения в данных.
        Аргументы: data - данные для проверки.
        Возвращает: валидированные данные.
        Ошибки валидации: если поле image отсутствует или равно None.
        """
        if data is None:
            raise serializers.ValidationError(
                {'image': 'Это поле обязательно.'})
        return data

    @staticmethod
    def _create_or_update_ingredients(recipe, ingredients_data):
        """Создает или обновляет ингредиенты в рецепте.
        Аргументы:
            - recipe - объект рецепта,
            - ingredients_data - данные ингредиентов.
        """
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        recipe.tags.set(tags)
        self._create_or_update_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        instance.tags.set(tags)
        instance.ingredients.clear()
        self._create_or_update_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReadRecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class SubscriptionsSerializer(CustomUserSerializer):
    """Сериализатор для подписок пользователя."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes',
                                                     'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов у пользователя."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Возвращает список рецептов пользователя.
        Есть возможность ограничения по количеству.
        Аргументы: obj - объект пользователя.
        Возвращает: список рецептов с кратким содержанием.
        """
        recipes = obj.recipes.all()
        recipes_limit = self.context.get('request'
                                         ).query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                raise ValidationError(
                    'Значение параметра recipes_limit должно быть числом.')
        return ShortRecipesSerializer(recipes, many=True).data


class ShortRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецептов."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания подписки на пользователя."""

    class Meta:
        model = Subscriptions
        fields = ('follower', 'following')

    def validate(self, data):
        """Проверяет, что пользователь не подписан на себя и не подписан на
        данного пользователя более одного раза.
        Аргументы: data - данные для проверки.
        Возвращает: валидированные данные.
        Ошибки валидации:
            - если пользователь пытается подписаться на себя,
            - если пользователь уже подписан.
        """
        follower = data['follower']
        following = data['following']
        if follower == following:
            raise ValidationError('Подписаться на самого себя невозможно.')
        if Subscriptions.objects.filter(
                follower=follower, following=following).exists():
            raise ValidationError(
                'Подписаться на пользователя можно только один раз.')
        return data

    def to_representation(self, instance):
        return SubscriptionsSerializer(
            instance.following, context=self.context).data


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания объекта в избранном."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.')
        return data

    def to_representation(self, instance):
        return ShortRecipesSerializer(instance.recipe).data


class ShoppingCartCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания объекта в корзине."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже добавлен в корзину.')
        return data

    def to_representation(self, instance):
        return ShortRecipesSerializer(instance.recipe).data
