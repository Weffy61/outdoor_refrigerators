from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .api_views import RefrigeratorMapView

urlpatterns = [
    path('refrigerators/', RefrigeratorMapView.as_view(), name='api-refrigerators'),
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
