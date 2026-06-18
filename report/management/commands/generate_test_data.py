import io
import random

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from PIL import Image

from report.models import Refrigerator, Report, Photo

User = get_user_model()

CITY_COORDS = {
    'Ростов':       (47.2357, 39.7015),
    'Батайск':      (47.1380, 39.7468),
    'Аксай':        (47.2718, 39.8737),
    'Новочеркасск': (47.4135, 40.0965),
    'Таганрог':     (47.2090, 38.9360),
    'Азов':         (47.1072, 39.4237),
}

CITY_KEYWORDS = list(CITY_COORDS.keys())

STATUSES = ['on_review', 'approved', 'approved', 'approved', 'decline']


def detect_city(address):
    if not address:
        return None
    for city in CITY_KEYWORDS:
        if city.lower() in address.lower():
            return city
    return None


def jitter(coord, scale=0.015):
    return coord + random.uniform(-scale, scale)


def make_dummy_image():
    img = Image.new('RGB', (64, 64), color=(180, 200, 220))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


class Command(BaseCommand):
    help = 'Привязывает торговых к менеджеру и генерирует GPS-отчёты по их холодильникам'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все отчёты и фото торговых представителей перед генерацией',
        )
        parser.add_argument(
            '--manager',
            type=str,
            default='admin@admin.ru',
            help='Email менеджера (по умолчанию admin@admin.ru)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Максимум холодильников на торгового (0 = без ограничения)',
        )

    def handle(self, *args, **options):
        manager_email = options['manager']
        limit = options['limit']

        try:
            manager = User.objects.get(email=manager_email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Менеджер {manager_email} не найден.'))
            return

        reps_qs = User.objects.filter(
            is_manager=False,
            manager__isnull=True,
        ).exclude(email='sklad@mail.ru')

        linked = reps_qs.update(manager=manager)
        if linked:
            self.stdout.write(f'Привязано к менеджеру {manager.email}: {linked} торговых')

        reps = list(User.objects.filter(
            is_manager=False,
            manager=manager,
        ).exclude(email='sklad@mail.ru'))

        if not reps:
            self.stdout.write(self.style.ERROR('Нет торговых представителей в базе.'))
            return

        self.stdout.write(f'Торговых представителей: {len(reps)}')

        if options['clear']:
            deleted_reports = Report.objects.filter(sender__in=reps).count()
            Report.objects.filter(sender__in=reps).delete()
            self.stdout.write(f'Удалено отчётов: {deleted_reports}')

        image_data = make_dummy_image()
        total_reports = 0
        total_photos = 0
        skipped = 0

        for rep in reps:
            fridges_qs = Refrigerator.objects.filter(
                is_assigned=rep,
            ).select_related('organization')

            if limit:
                fridges_qs = fridges_qs[:limit]

            fridges = list(fridges_qs)

            for fridge in fridges:
                address = getattr(fridge.organization, 'address', '') or ''
                city = detect_city(address)
                if not city:
                    skipped += 1
                    continue

                clat, clon = CITY_COORDS[city]

                for _ in range(random.randint(2, 3)):
                    report = Report.objects.create(
                        refrigerator=fridge,
                        sender=rep,
                        status=random.choice(STATUSES),
                        date=timezone.now() - timedelta(days=random.randint(1, 180)),
                    )
                    for _ in range(random.randint(1, 2)):
                        photo = Photo(
                            report=report,
                            latitude=round(jitter(clat), 6),
                            longitude=round(jitter(clon), 6),
                        )
                        fname = f'gps_{rep.pk}_{city}_{report.pk}_{random.randint(0, 9999)}.jpg'
                        photo.image.save(fname, ContentFile(image_data), save=False)
                        photo.save()
                        total_photos += 1

                    total_reports += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово: {total_reports} отчётов, {total_photos} фото с GPS.'
            f' Холодильников без города: {skipped}.'
        ))
