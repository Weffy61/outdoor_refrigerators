import pandas as pd
from django.core.management.base import BaseCommand
from report.models import Refrigerator, Organization


class Command(BaseCommand):
    help = 'Импорт холодильного оборудования и партнеров из Excel файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        data = pd.read_excel(file_path)

        for index, row in data.iterrows():
            serial_number = row['Серийный номер']
            model = row['Оборудование']
            partner = row.get('Партнер')
            responsible = row.get('Ответственный')

            try:
                if pd.isna(partner):
                    name, address = 'Склад', 'Склад'
                elif ' / ' in partner:
                    name, address = partner.split(' / ', 1)
                else:
                    name, address = partner, ''

                organization, created = Organization.objects.get_or_create(name=name, defaults={'address': address})

                Refrigerator.objects.create(
                    serial_number=serial_number,
                    model=model,
                    organization=organization,
                    is_assigned=None
                )
            except (TypeError, ValueError, AttributeError) as error:
                print(f'Нее импортирована строка {index + 1}, потому что {error}')
                print(partner)
                print(type(partner))
                continue

        self.stdout.write(self.style.SUCCESS('Данные успешно импортированы'))
