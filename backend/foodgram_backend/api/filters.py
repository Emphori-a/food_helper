from django_filters import rest_framework

from recipes.models import Ingredient


class IngredientFilterSet(rest_framework.FilterSet):
    name = rest_framework.CharFilter(field_name='name',
                                     lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
