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
        verbose_name='Организация расположения оборудования'
    )

    class Meta:
        verbose_name = 'Холодильник'
        verbose_name_plural = 'Холодильники'

    def __str__(self):
        return f'Холодильник {self.model} {self.serial_number}'


class Organization(models.Model):
    name = models.CharField(verbose_name='Название организации', max_length=200)
    address = models.TextField(verbose_name='Адрес организации', null=True, blank=True)

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'

    def __str__(self):
        return self.name


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
        choices=STATUS_CHOICES
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

    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'

    def __str__(self):
        return f'Отчет {self.date} для {self.refrigerator}'


class Photo(models.Model):
    report = models.ForeignKey(
        'Report',
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Отчет'
    )
    image = models.ImageField(upload_to='report_photos/', verbose_name='Фото отчета')

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'

    def __str__(self):
        return f'Фото для отчета {self.report}'
