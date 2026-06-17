from rest_framework import serializers

from .models import Refrigerator, Photo


class RefrigeratorMapSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_address = serializers.CharField(source='organization.address', read_only=True)
    assigned_to = serializers.SerializerMethodField()
    last_report_status = serializers.SerializerMethodField()
    last_report_date = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Refrigerator
        fields = [
            'id', 'serial_number', 'model',
            'organization_name', 'organization_address',
            'assigned_to', 'last_report_status', 'last_report_date',
            'latitude', 'longitude',
        ]

    def get_assigned_to(self, obj):
        if obj.is_assigned:
            return f'{obj.is_assigned.first_name} {obj.is_assigned.last_name}'
        return None

    def get_last_report_status(self, obj):
        last = obj.reports.last()
        return last.status if last else None

    def get_last_report_date(self, obj):
        last = obj.reports.last()
        return last.date if last else None

    def _last_photo_with_coords(self, obj):
        return Photo.objects.filter(
            report__refrigerator=obj,
            latitude__isnull=False,
            longitude__isnull=False,
        ).order_by('-report__date').first()

    def get_latitude(self, obj):
        photo = self._last_photo_with_coords(obj)
        return float(photo.latitude) if photo else None

    def get_longitude(self, obj):
        photo = self._last_photo_with_coords(obj)
        return float(photo.longitude) if photo else None
