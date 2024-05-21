from django.contrib import admin
from .models import Refrigerator, Report, Photo, Organization


@admin.register(Refrigerator)
class RefrigeratorAdmin(admin.ModelAdmin):
    list_display = ['model', 'serial_number', 'get_organization']
    raw_id_fields = ['is_assigned', 'organization']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['date']
    raw_id_fields = ['refrigerator', 'sender']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'address']


admin.register(Photo)
