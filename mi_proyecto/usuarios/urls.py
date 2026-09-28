from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login-password/', views.login_view, name='login_password'),
    path('solicitar-acceso/', views.login_view, name='solicitar_acceso'),
    path('validar-pin/', views.legacy_pin_redirect, name='validar_pin'),
    path('reenviar-pin/', views.legacy_pin_redirect, name='reenviar_pin'),
    path('registro/', views.registro_view, name='registro'),
    path('recuperar-password/', auth_views.PasswordResetView.as_view(
        template_name='usuarios/password_reset/password_reset_form.html',
        email_template_name='usuarios/password_reset/password_reset_email.txt',
        subject_template_name='usuarios/password_reset/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('recuperar-password/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='usuarios/password_reset/password_reset_done.html'), name='password_reset_done'),
    path('restablecer-password/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='usuarios/password_reset/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('restablecer-password/completo/', auth_views.PasswordResetCompleteView.as_view(
        template_name='usuarios/password_reset/password_reset_complete.html'), name='password_reset_complete'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('api/crear-ticket/', views.crear_ticket_view, name='crear_ticket'),
    path('emails/', views.email_preview_view, name='email_preview_default'),
    path('emails/<str:plantilla>/', views.email_preview_view, name='email_preview'),
]
