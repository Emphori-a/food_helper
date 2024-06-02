import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Load data from a JSON file into the Ingredient table'

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='Имя JSON файла')

    def handle(self, *args, **options):
        try:
            with open(os.path.join(DATA_ROOT, options['file_name']),
                      mode='r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    Ingredient.objects.get_or_create(
                        name=item['name'],
                        measurement_unit=item['measurement_unit'],
                    )
            self.stdout.write(self.style.SUCCESS('Данные успешно загружены.'))
        except FileNotFoundError:
            raise CommandError(
                'Указанный файл должен находиться в директории data.'
            )
