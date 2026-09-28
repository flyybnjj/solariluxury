from django.contrib import admin
from .models import Categoria, Producto, Talla, ProductoTalla, DetalleProducto, ImagenProducto, PreOrden, Pedido, Tracker


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'slug')
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}


class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 3
    min_num = 0


class ProductoTallaInline(admin.TabularInline):
    model = ProductoTalla
    extra = 2
    min_num = 0


class DetalleProductoInline(admin.TabularInline):
    model = DetalleProducto
    extra = 2
    min_num = 0


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'precio', 'precio_usd', 'badge_estado', 'categoria', 'creado_en')
    list_filter = ('badge_estado', 'categoria')
    search_fields = ('nombre', 'descripcion', 'subtitulo')
    list_editable = ('badge_estado',)
    inlines = [ImagenProductoInline, ProductoTallaInline, DetalleProductoInline]
    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre', 'subtitulo', 'categoria', 'imagen')
        }),
        ('Precios y Estado', {
            'fields': ('precio', 'precio_usd', 'badge_estado')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
    )


@admin.register(Talla)
class TallaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(ProductoTalla)
class ProductoTallaAdmin(admin.ModelAdmin):
    list_display = ('producto', 'talla', 'stock')
    list_filter = ('talla',)
    search_fields = ('producto__nombre', 'talla__nombre')


@admin.register(DetalleProducto)
class DetalleProductoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'texto', 'orden')
    list_filter = ('producto',)
    search_fields = ('texto', 'producto__nombre')
    ordering = ('producto', 'orden')


@admin.register(ImagenProducto)
class ImagenProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'titulo', 'imagen', 'orden')
    list_filter = ('producto',)
    search_fields = ('titulo', 'imagen', 'producto__nombre')
    ordering = ('producto', 'orden')


@admin.register(PreOrden)
class PreOrdenAdmin(admin.ModelAdmin):
    list_display = ('codigo_orden', 'usuario', 'nombre_cliente', 'email_cliente', 'producto', 'talla', 'precio_total', 'estado', 'dhl_tracking', 'fecha_creacion')
    list_filter = ('estado', 'ciudad')
    search_fields = ('codigo_orden', 'nombre_cliente', 'email_cliente', 'dhl_tracking', 'producto__nombre')
    list_editable = ('estado',)
    readonly_fields = ('codigo_orden', 'fecha_creacion')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('codigo_pedido', 'usuario', 'email', 'nombre_cliente', 'producto', 'talla', 'precio_total', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'ciudad')
    search_fields = ('codigo_pedido', 'email', 'nombre_cliente', 'producto__nombre')
    list_editable = ('estado',)
    readonly_fields = ('codigo_pedido', 'fecha_creacion')


@admin.register(Tracker)
class TrackerAdmin(admin.ModelAdmin):
    list_display = ('numero_guia', 'courier', 'usuario', 'email', 'estado_envio', 'ubicacion_actual', 'destino', 'porcentaje_avance', 'fecha_actualizacion')
    list_filter = ('courier', 'estado_envio')
    search_fields = ('numero_guia', 'email', 'ubicacion_actual', 'destino')
    list_editable = ('estado_envio', 'ubicacion_actual', 'porcentaje_avance')
    readonly_fields = ('fecha_actualizacion',)


