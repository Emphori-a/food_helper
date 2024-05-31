from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.constans import MAX_LENGTH_NAME


class User(AbstractUser):
    """
    Класс пользователя.

    Атрибуты:
        username (str): Имя пользователя, уникальное.
        email (str): Адрес электронной почты, уникальный.
        first_name (str): Имя.
        last_name (str): Фамилия.
        avatar (ImageField): Аватар пользователя, необязательное поле.
    """

    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_LENGTH_NAME,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_NAME,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_NAME,
    )
    avatar = models.ImageField(
        verbose_name='Аватар пользователя',
        upload_to='avatars/',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        """Возвращает строковое представление пользователя."""
        return self.username


class Subscriptions(models.Model):
    """Класс, реализующий подписки пользователей друг на друга.

    Атрибуты:
        follower (User): Подписчик
        following (User): Автор, на которого подписан пользователь.

    В модели установлены ограничения:
        - подписаться на пользователя можно только один раз.
        - подписаться на самого себя нельзя.
    """
    follower = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='followers'
    )
    following = models.ForeignKey(
        User,
        verbose_name='Автор, на которого подписан',
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['follower_id', 'following_id'],
                name='unique_follower_following',
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F("following")),
                name='user_cant_self_follow',
            )
        ]
