from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from . import admin_views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login-password/', views.login_view, name='login_password'),
    path('solicitar-acceso/', views.login_view, name='solicitar_acceso'),
    path('validar-pin/', views.legacy_pin_redirect, name='validar_pin'),
    path('reenviar-pin/', views.legacy_pin_redirect, name='reenviar_pin'),
    path('registro/', views.registro_view, name='registro'),
    path('recuperar-password/', views.password_reset_request, name='password_reset'),
    path('recuperar-password/enviado/', views.password_reset_done, name='password_reset_done'),
    path('recuperar-password/verificar/', views.password_reset_verify, name='password_reset_verify'),
    path('restablecer-password/codigo/', views.password_reset_code_confirm, name='password_reset_code_confirm'),
    path('restablecer-password/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='usuarios/password_reset/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('restablecer-password/completo/', auth_views.PasswordResetCompleteView.as_view(
        template_name='usuarios/password_reset/password_reset_complete.html'), name='password_reset_complete'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('admin-panel/usuarios/', admin_views.admin_users, name='admin_users'),
    path('admin-panel/usuarios/nuevo/', admin_views.admin_user_create, name='admin_user_create'),
    path('admin-panel/usuarios/<int:user_id>/editar/', admin_views.admin_user_edit, name='admin_user_edit'),
    path('admin-panel/usuarios/<int:user_id>/eliminar/', admin_views.admin_user_delete, name='admin_user_delete'),
    path('api/crear-ticket/', views.crear_ticket_view, name='crear_ticket'),
    path('emails/', views.email_preview_view, name='email_preview_default'),
    path('emails/<str:plantilla>/', views.email_preview_view, name='email_preview'),
]
