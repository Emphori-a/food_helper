from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilterSet(FilterSet):
    """Класс фильтрации для ингредиентов.
    Поиск ингредиентов ведется по вхождению в начало названия.
    """

    name = filters.CharFilter(field_name='name',
                              lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilterSet(FilterSet):
    """Класс фильтрации для рецептов.
    Фильтрация возможна по нескольким полям:
        - по тегам,
        - по автору рецепта,
        - фильтрация рецептов, находящихся в избранном пользователя,
        - фильтрация рецептов, находящихся в списке покупок пользователя.
    """

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorite__user=user)
        return queryset
