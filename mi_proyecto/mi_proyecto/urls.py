from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalogo.urls')),
    path('locales/', include('locales.urls')),
    path('', include('usuarios.urls')),
]