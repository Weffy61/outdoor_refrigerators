from django.contrib import admin
from django.db.models import Window, F
from django.db.models.functions import RowNumber
from django.shortcuts import redirect, render
from django.urls import path

from .forms import AssignUserForm
from .models import Refrigerator, Report, Photo, Organization
from .service import check_exif


@admin.register(Refrigerator)
class RefrigeratorAdmin(admin.ModelAdmin):
    list_display = ['model', 'serial_number', 'get_organization', 'get_employee', 'get_last_date_report']
    raw_id_fields = ['is_assigned', 'organization']
    search_fields = ['model', 'serial_number', 'is_assigned__first_name', 'is_assigned__last_name']
    actions = ['assign_user']

    def assign_user(self, request, queryset):
        form = None
        if 'apply' in request.POST:

            form = AssignUserForm(request.POST)

            if form.is_valid():
                user = form.cleaned_data['user']
                count = queryset.update(is_assigned=user)

                self.message_user(request, f'{count} холодильников(а) было успешно закреплено за {user}.')
                return redirect(request.get_full_path())
        if not form:
            form = AssignUserForm(initial={'_selected_action': queryset.values_list('id', flat=True)})
        return render(request, 'admin/assign_user.html', {
            'items': queryset,
            'form': form,
            'title': 'Выбрать ответственного'})

    assign_user.short_description = 'Выбрать ответственного'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('assign_user/', self.admin_site.admin_view(self.assign_user), name='assign_user'),
        ]
        return custom_urls + urls


class PhotoInline(admin.TabularInline):
    model = Photo
    readonly_fields = ['image_tag']
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['date', 'get_customer_name', 'get_refrigerator', 'manager_review', 'status']
    raw_id_fields = ['refrigerator', 'sender']
    readonly_fields = ['exif_description', 'date']
    search_fields = [
        'refrigerator__model',
        'refrigerator__serial_number',
        'sender__first_name',
        'sender__last_name',
    ]
    inlines = [PhotoInline]
    change_form_template = 'admin/exif_meta.html'

    def response_change(self, request, obj):
        if "_check_exif" in request.POST:
            photos = obj.photos.all()

            if photos.exists():
                exif_reports = [f'Отчет по файлу {index}:\n {check_exif(request.build_absolute_uri(photo.image.url))}'
                                for index, photo in enumerate(photos, start=1)]
                obj.exif_description = "\n\n\n\n".join(exif_reports)
                obj.save()
                self.message_user(request, 'Отчет сформирован')
            else:
                self.message_user(request, 'Фото не найдено', level='error')
            return redirect(".")
        return super().response_change(request, obj)


class RefrigeratorInline(admin.TabularInline):
    model = Refrigerator
    extra = 1


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['display_order', 'name', 'address', 'get_total_refrigerators']
    search_fields = ['name']
    inlines = [RefrigeratorInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(display_order=Window(
            expression=RowNumber(),
            order_by=F('id').desc()
        ))
        return queryset

    def display_order(self, obj):
        return obj.display_order

    display_order.admin_order_field = 'display_order'
    display_order.short_description = '№'


admin.register(Photo)

