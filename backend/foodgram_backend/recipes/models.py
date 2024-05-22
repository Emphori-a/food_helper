from django.db import models

TAG_LENGTH = 32
INGREDIENT_LENGTH = 128
MEASUREMENT_LENGTH = 64


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
    """Класс для описания ингридиентов рецептов."""

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
