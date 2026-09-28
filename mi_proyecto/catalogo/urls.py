from django.urls import path
from . import views
from locales import views as locales_views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('api/solicitar-key/', views.solicitar_key, name='solicitar_key'),
    path('api/validar-key/', views.validar_key, name='validar_key'),
    path('bloquear-tienda/', views.bloquear_tienda, name='bloquear_tienda'),
    path('api/rastrear-pedido/', locales_views.api_rastrear, name='api_rastrear_pedido'),
    path('api/crear-preorden/', locales_views.api_crear_preorden, name='api_crear_preorden_direct'),
    path('api/dolar/', locales_views.api_dolar, name='api_dolar'),
]
