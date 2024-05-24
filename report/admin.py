from django.contrib import admin
from django.shortcuts import redirect

from .models import Refrigerator, Report, Photo, Organization
from .service import check_exif


@admin.register(Refrigerator)
class RefrigeratorAdmin(admin.ModelAdmin):
    list_display = ['model', 'serial_number', 'get_organization']
    raw_id_fields = ['is_assigned', 'organization']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['date']
    raw_id_fields = ['refrigerator', 'sender']
    readonly_fields = ['exif_description']
    change_form_template = 'admin/exif_meta.html'

    def response_change(self, request, obj):
        if "_check_exif" in request.POST:
            photos = obj.photos.all()

            if photos.exists():
                exif_reports = [f'Отчет по файлу {index}: {check_exif(request.build_absolute_uri(photo.image.url))}' for
                                index, photo in enumerate(photos, start=1)]
                obj.exif_description = "\n\n\n\n".join(exif_reports)
                obj.save()
                self.message_user(request, 'Отчет сформирован')
            else:
                self.message_user(request, 'Фото не найдено', level='error')
            return redirect(".")
        return super().response_change(request, obj)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'address']


admin.register(Photo)
