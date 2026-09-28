from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_locales, name='lista_locales'),
    path('informacion/', views.informacion, name='informacion'),
    path('crear-preorden/', views.crear_preorden, name='crear_preorden'),
    path('api/rastrear/', views.api_rastrear, name='api_rastrear'),
    path('api/crear-preorden/', views.api_crear_preorden, name='api_crear_preorden'),
]