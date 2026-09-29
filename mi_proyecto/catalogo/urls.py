from django.urls import path
from . import views
from locales import views as locales_views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('preguntas-frecuentes/', views.preguntas_frecuentes, name='preguntas_frecuentes'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('bloquear-tienda/', views.bloquear_tienda, name='bloquear_tienda'),
    path('api/rastrear-pedido/', locales_views.api_rastrear, name='api_rastrear_pedido'),
    path('api/crear-preorden/', locales_views.api_crear_preorden, name='api_crear_preorden_direct'),
    path('api/validar-cupon/', locales_views.api_validar_cupon, name='api_validar_cupon_direct'),
    path('api/dolar/', locales_views.api_dolar, name='api_dolar'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/productos/', views.admin_productos, name='admin_productos'),
    path('admin-panel/productos/crear/', views.admin_crear_producto, name='admin_crear_producto'),
    path('admin-panel/productos/<int:producto_id>/editar/', views.admin_editar_producto, name='admin_editar_producto'),
    path('admin-panel/productos/<int:producto_id>/eliminar/', views.admin_eliminar_producto, name='admin_eliminar_producto'),
]
