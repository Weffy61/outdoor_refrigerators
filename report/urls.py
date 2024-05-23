from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('reports/', views.get_reports, name='reports'),
    path('report/<int:report_id>', views.get_report, name='report'),
    path('create_report/', views.create_report, name='create_report'),
    path('create_report/<int:refrigerator_id>/', views.create_report, name='create_report_with_refrigerator'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)