from django.contrib import admin
from .models import Refrigerator, Report, Photo


@admin.register(Refrigerator)
class RefrigeratorAdmin(admin.ModelAdmin):
    list_display = ['model', 'organization', 'organization_address']
    raw_id_fields = ['is_assigned']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['date']
    raw_id_fields = ['refrigerator', 'sender']


admin.register(Photo)
