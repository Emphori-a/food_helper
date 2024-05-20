from django.db import models
from django.contrib.auth.models import AbstractUser

from .validators import validate_username

MAX_LENGTH_NAME = 150


class User(AbstractUser):
    """Класс пользователя."""

    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_LENGTH_NAME,
        unique=True,
        validators=[validate_username],
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_NAME,
        blank=True
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_NAME,
        blank=True
    )
    avatar = models.ImageField(
        verbose_name='Аватар пользователя',
        upload_to='media/users/',
        blank=True,
        null=True
    )