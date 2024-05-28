import csv
import os

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser

from recipes.models import Ingredient, Tag

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Load data from a CSV file into the Ingredient or Tag table'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('file_name', type=str, help='Имя CSV файла')

    def handle(self, *args, **options):
        file_name = options['file_name']
        file_path = os.path.join(DATA_ROOT, file_name)
        if not os.path.isfile(file_path):
            raise CommandError(
                'Указанный файл должен находиться в директории data.'
            )
        if 'ingredient' in file_name.lower():
            self.load_ingredients(file_path)
        elif 'tag' in file_name.lower():
            self.load_tags(file_path)
        else:
            raise CommandError(
                'Имя файла должно содержать "ingredient" или "tag".')

    def load_ingredients(self, file_path):
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    name, measurement_unit = row
                    Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
            self.stdout.write(self.style.SUCCESS(
                'Ингредиенты успешно загружены.'))
        except Exception as e:
            raise CommandError(f'Ошибка при загрузке ингредиентов: {e}')

    def load_tags(self, file_path):
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    name, slug = row
                    Tag.objects.get_or_create(
                        name=name,
                        slug=slug
                    )
            self.stdout.write(self.style.SUCCESS('Теги успешно загружены.'))
        except Exception as e:
            raise CommandError(f'Ошибка при загрузке тегов: {e}')
