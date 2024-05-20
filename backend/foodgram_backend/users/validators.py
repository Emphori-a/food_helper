import re

from django.core.exceptions import ValidationError

REGEX_FOR_USERNAME = r'^[\w.@+-]+\Z'


def validate_username(value):
    """Функция валидации поля username."""
    invalid_chars = [char for char in value
                     if not re.search(REGEX_FOR_USERNAME, char)]
    if invalid_chars:
        raise ValidationError('Имя пользователя может содержать только буквы, '
                              'цифры и знаки @ / . / + / -, некорректные '
                              f'символы: {invalid_chars}')
