import csv
import os

from django.core.management.base import BaseCommand
from foodgram.settings import BASE_DIR

from recipes.models import Ingredient


def ingredients_down(path):
    with open(path, encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        print('Creating ingredients ...')
        for row in reader:
            Ingredient.objects.create(
                name=row[0],
                measurement_unit=row[1]
            )
        print('done')


class Command(BaseCommand):
    help = 'Loads ingredients from CSV file'

    def handle(self, *args, **options):
        path_to_file = os.path.join(BASE_DIR, 'backend/data/ingredients.csv')
        print(path_to_file)
        ingredients_down(path_to_file)
