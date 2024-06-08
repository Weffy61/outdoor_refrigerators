import pandas as pd
from django.core.management.base import BaseCommand
from report.models import Refrigerator, Organization
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Импорт холодильного оборудования и партнеров из Excel файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        data = pd.read_excel(file_path)
        sklad_user = CustomUser.objects.get(email='sklad@mail.ru')

        for index, row in data.iterrows():
            serial_number = row['Серийный номер']
            model = row['Оборудование']
            partner = row.get('Партнер')
            responsible = row.get('Ответственный')
            line = index + 1

            try:
                if pd.isna(partner):
                    name, address = 'Склад', 'Склад'
                elif '/' in partner:
                    name, address = partner.split('/', 1)
                else:
                    name, address = partner, ''

                organization, _ = Organization.objects.get_or_create(name=name, defaults={'address': address})

                refrigerator, created = Refrigerator.objects.get_or_create(
                    serial_number=serial_number,
                    defaults={
                        'model': model,
                        'organization': organization,
                    }
                )
                if pd.isna(responsible):
                    continue
                else:
                    try:
                        last_name, first_name = responsible.split()
                        first_name = first_name.strip()
                        last_name = last_name.strip()
                    except ValueError:
                        print(f'Не удалось разделить имя и фамилию для строки {line}: {responsible}')
                        continue
                    if (first_name == 'Роман' and last_name == 'Диденко') or \
                       (first_name == 'Эдуард' and last_name == 'Янцевич') or \
                       (refrigerator.organization.name == 'Склад'):
                        assigned_user = sklad_user
                    else:
                        assigned_user = CustomUser.objects.get(first_name=first_name, last_name=last_name)

                    if created:
                        refrigerator.is_assigned = assigned_user
                        refrigerator.save()
                    if not created:
                        refrigerator.organization = organization
                        refrigerator.is_assigned = assigned_user
                        refrigerator.model = model
                        refrigerator.save()

            except (TypeError, ValueError, AttributeError) as error:
                print(f'Не импортирована строка {line}, потому что {error}')
                print(partner)
                print(type(partner))
                continue

        self.stdout.write(self.style.SUCCESS('Данные успешно импортированы'))
