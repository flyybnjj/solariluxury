from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/img/logo_marca.png', permanent=True), name='favicon'),
    path('admin/', admin.site.urls),
    path('', include('catalogo.urls')),
    path('locales/', include('locales.urls')),
    path('', include('usuarios.urls')),
]
