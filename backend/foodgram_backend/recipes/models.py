from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

TAG_LENGTH = 32
INGREDIENT_LENGTH = 128
MEASUREMENT_LENGTH = 64
RECIPE_LENGTH = 256

User = get_user_model()


class Tag(models.Model):
    """Класс для описания тэгов рецептов."""

    name = models.CharField(
        verbose_name='Наименование',
        max_length=TAG_LENGTH,
    )
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=TAG_LENGTH,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Тэги'

    def __str__(self) -> str:
        return self.slug


class Ingredient(models.Model):
    """Класс для описания ингредиентов рецептов."""

    name = models.CharField(
        verbose_name='Наименование',
        max_length=INGREDIENT_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MEASUREMENT_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=RECIPE_LENGTH
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        verbose_name='Фото',
        upload_to='recipes/',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        help_text='Укажите время приготовления в минутах',
        validators=[
            MinValueValidator(1, message='Минимальное значение поля - 1.')
        ]
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        related_name='recipes',
        through='IngredientInRecipe'
    )
    is_favorited = models.BooleanField(
        verbose_name='Рецепт находится в избранном',
        blank=True,
        default=False
    )
    is_in_shopping_cart = models.BooleanField(
        verbose_name='Рецепт находится в корзине',
        blank=True,
        default=False
    )
    short_link = models.CharField(
        verbose_name='Короткая ссылка на рецепт',
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )


class IngredientInRecipe(models.Model):
    """Класс для описания ингредиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='ingredients_in',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='in_recipes',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1, message='Количество должно быть больше 0.')
        ]
    )

    class Meta:
        verbose_name = 'Ингредент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self) -> str:
        return f'{self.recipe.name}: {self.amount} {self.ingredient.name}'
