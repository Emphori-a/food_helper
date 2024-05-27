import re

from django.core.exceptions import ValidationError

from core.constans import REGEX_FOR_USERNAME


def validate_username(value: str) -> None:
    """
    Функция валидации поля username.

    Аргументы:
        value (str): Значение поля username, которое нужно валидировать.

    Исключения:
        ValidationError: Если значение содержит некорректные символы.
    """
    invalid_chars = [char for char in value
                     if not re.search(REGEX_FOR_USERNAME, char)]
    if invalid_chars:
        raise ValidationError('Имя пользователя может содержать только буквы, '
                              'цифры и знаки @ / . / + / -, некорректные '
                              f'символы: {invalid_chars}')
