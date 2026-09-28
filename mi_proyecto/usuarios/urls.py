from django.urls import path
from . import views

urlpatterns = [
    # Passwordless Login / OTP
    path('solicitar-acceso/', views.solicitar_acceso_view, name='solicitar_acceso'),
    path('validar-pin/', views.validar_pin_view, name='validar_pin'),
    path('reenviar-pin/', views.reenviar_pin_view, name='reenviar_pin'),

    # Autenticación principal
    path('login/', views.solicitar_acceso_view, name='login'),
    path('login-password/', views.login_view, name='login_password'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('api/crear-ticket/', views.crear_ticket_view, name='crear_ticket'),

    # Vista previa interactiva de correos Apple Style y envío de pruebas
    path('emails/', views.email_preview_view, name='email_preview_default'),
    path('emails/<str:plantilla>/', views.email_preview_view, name='email_preview'),
    path('api/enviar-email-prueba/', views.enviar_email_prueba_view, name='enviar_email_prueba'),
]
