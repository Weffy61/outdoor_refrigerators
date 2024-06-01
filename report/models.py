import os
from datetime import datetime

from PIL import Image
from django.db import models
from django.utils import timezone

from users.models import CustomUser


class Refrigerator(models.Model):
    is_assigned = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refrigerators',
        verbose_name='Закреплен за'
    )
    serial_number = models.CharField(verbose_name='Серийный номер', max_length=200)
    model = models.CharField(verbose_name='Модель аппарата', max_length=200)
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name='Организация расположения оборудования'
    )

    class Meta:
        verbose_name = 'Холодильник'
        verbose_name_plural = 'Холодильники'

    def __str__(self):
        return f'Холодильник {self.model} {self.serial_number}'

    def get_organization(self):
        if self.organization:
            return self.organization.name
        else:
            return 'Организация отсутствует'
    get_organization.short_description = 'Организация расположения ХО'

    def get_last_date_report(self):
        if self.reports.last():
            return self.reports.last().date
        else:
            return 'Отчет отсутствует'
    get_last_date_report.short_description = 'Дата последнего отчета'

    def get_employee(self):
        if self.is_assigned:
            return f'{self.is_assigned.first_name} {self.is_assigned.last_name}'
        else:
            return 'Закрепленный ответственный отсутствует'

    get_employee.short_description = 'Ответственный за ХО'


class Organization(models.Model):
    name = models.CharField(verbose_name='Название организации', max_length=200)
    address = models.TextField(verbose_name='Адрес организации', null=True, blank=True)

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'

    def __str__(self):
        return self.name

    def get_total_refrigerators(self):
        if self.organizations:
            return self.organizations.all().count()
        else:
            return 'ХО отсутствует'
    get_total_refrigerators.short_description = 'Закреплено всего ХО'


class Report(models.Model):
    date = models.DateTimeField(verbose_name='Дата и время отчета', db_index=True, default=timezone.now)
    STATUS_CHOICES = [
        ('on_review', 'На рассмотрении'),
        ('approved', 'Одобрен'),
        ('decline', 'Отклонен')
    ]
    status = models.CharField(
        verbose_name='Статус отчета',
        max_length=100,
        db_index=True,
        choices=STATUS_CHOICES,
        default='on_review'
    )
    refrigerator = models.ForeignKey(
        Refrigerator,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
        verbose_name='Холодильник'
    )

    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
        verbose_name='Отчет отправил',
    )
    comment = models.TextField(verbose_name='Комментарий от торгового представителя', blank=True, null=True)
    comment_manager = models.TextField(verbose_name='Комментарий от менеджера', blank=True, null=True)
    comment_admin = models.TextField(verbose_name='Комментарий от админа', blank=True, null=True)
    exif_description = models.TextField(
        verbose_name='Результат проверки EXIF',
        blank=True,
        null=True,
    )
    MANAGER_REVIEW_CHOICES = [
        ('approve', 'Одобрено'),
        ('decline', 'Отклонено')
    ]
    manager_review = models.CharField(
        verbose_name='Рецензия менеджера',
        max_length=100,
        choices=MANAGER_REVIEW_CHOICES,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'
        ordering = ["-date"]

    def __str__(self):
        return f'Отчет {self.date} для {self.refrigerator}'

    def get_customer_name(self):
        if self.sender:
            return f'{self.sender.first_name} {self.sender.last_name}'
        else:
            return 'Торговый представитель отстутствует'
    get_customer_name.short_description = 'Торговый представитель'

    def get_refrigerator(self):
        if self.refrigerator:
            return f'{self.refrigerator.model} {self.refrigerator.serial_number}'
        else:
            return 'Холодильное оборудование отсутствует'
    get_refrigerator.short_description = 'Холодильное оборудование'


class Photo(models.Model):
    report = models.ForeignKey(
        'Report',
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Отчет'
    )

    image = models.ImageField(
        upload_to='report_photos/',
        verbose_name='Фото отчета'
    )

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'

    def __str__(self):
        return f'Фото для отчета {self.report}'

    def get_upload_path(self, filename):
        today = datetime.today()
        date_path = today.strftime('%d.%m.%Y')
        path = os.path.join('report_photos', date_path)
        return path

    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            exif = img.info.get('exif')
            self.image.field.upload_to = self.get_upload_path(self.image.name)
            self.image.save(self.image.name, self.image, save=False)
            if exif:
                img = Image.open(self.image.path)
                img.save(self.image.path, exif=exif)

        super().save(*args, **kwargs)
