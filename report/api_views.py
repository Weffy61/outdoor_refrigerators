from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Refrigerator
from .serializers import RefrigeratorMapSerializer


@extend_schema(
    summary='Список холодильников с координатами',
    description=(
        'Возвращает холодильники текущего пользователя с последними известными '
        'GPS-координатами из EXIF-данных фотографий отчётов. '
        'Менеджер видит холодильники всех своих подчинённых.'
    ),
    parameters=[
        OpenApiParameter(
            name='with_coords',
            description='Если true — возвращает только холодильники с координатами',
            required=False,
            type=bool,
        )
    ],
    responses={200: RefrigeratorMapSerializer(many=True)},
    tags=['Холодильники'],
)
class RefrigeratorMapView(generics.ListAPIView):
    serializer_class = RefrigeratorMapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            qs = Refrigerator.objects.filter(
                is_assigned__in=user.subordinates.all()
            )
        else:
            qs = Refrigerator.objects.filter(is_assigned=user)

        qs = qs.select_related('organization', 'is_assigned').prefetch_related('reports')

        if self.request.query_params.get('with_coords') == 'true':
            qs = qs.filter(reports__photos__latitude__isnull=False).distinct()

        return qs
