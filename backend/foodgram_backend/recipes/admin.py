from django.contrib import admin

from core.constans import ADMIN_LIST_PER_PAGE

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_per_page = ADMIN_LIST_PER_PAGE
    list_display_links = ('name',)
    search_fields = ('name', 'slug')
    list_filter = ('slug',)


@admin.register(Ingredient)
class Ingredient(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_per_page = ADMIN_LIST_PER_PAGE
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


class IngredientInRecipeInline(admin.StackedInline):
    model = IngredientInRecipe
    extra = 0
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_count')
    readonly_fields = ('favorite_count',)
    list_per_page = ADMIN_LIST_PER_PAGE
    list_display_links = ('name',)
    search_fields = ('name', 'author')
    list_filter = ('tags',)
    inlines = (IngredientInRecipeInline,)

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        """Возвращает общее число добавлений этого рецепта в избранное."""
        return obj.in_favorite.count()


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_per_page = ADMIN_LIST_PER_PAGE
    list_display_links = ('recipe',)
    list_filter = ('recipe',)
    search_fields = ('ingredient',)


class FavoriteOrShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_per_page = ADMIN_LIST_PER_PAGE
    list_display_links = ('user',)
    list_filter = ('recipe',)
    search_fields = ('user',)


admin.site.register(ShoppingCart, FavoriteOrShoppingCartAdmin)
admin.site.register(Favorite, FavoriteOrShoppingCartAdmin)
