from django.contrib import admin
from .models import Local


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'tipo', 'direccion', 'horario', 'telefono', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre', 'direccion', 'telefono')
    list_editable = ('activo',)
