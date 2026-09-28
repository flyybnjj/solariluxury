from django.contrib import admin
from .models import Cliente, TicketSoporte


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ()

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Correo Electrónico'


@admin.register(TicketSoporte)
class TicketSoporteAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'email', 'contacto_alternativo', 'motivo', 'estado', 'creado_en')
    list_filter = ('estado', 'motivo', 'creado_en')
    search_fields = ('codigo', 'nombre', 'email', 'contacto_alternativo', 'mensaje')
    readonly_fields = ('codigo', 'creado_en')
