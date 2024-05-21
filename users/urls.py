from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy
from .views import CustomLoginView, RegisterView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('registration/', RegisterView.as_view(), name='registration'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('login')), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
