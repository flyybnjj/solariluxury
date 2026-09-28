from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Talla(models.Model):
    nombre = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = "Talla"
        verbose_name_plural = "Tallas"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    BADGE_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('AGOTADO', 'Agotado'),
        ('LIMITED DROP', 'Limited Drop'),
    ]

    nombre = models.CharField(max_length=255)
    subtitulo = models.CharField(max_length=255, blank=True)
    precio = models.PositiveIntegerField(help_text="Precio en CLP")
    precio_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True)
    imagen = models.CharField(max_length=255, default='img/placeholder.jpg')
    codigo_estilo = models.CharField(max_length=50, blank=True, null=True, help_text="Código de estilo o SKU oficial")
    color = models.CharField(max_length=100, blank=True, null=True, help_text="Colorway oficial")
    badge_estado = models.CharField(max_length=20, choices=BADGE_CHOICES, default='DISPONIBLE')
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )
    tallas = models.ManyToManyField(Talla, through='ProductoTalla', blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['id']

    def precio_formateado(self):
        return f"${self.precio:,}".replace(',', '.')

    def get_galeria(self):
        """Devuelve lista de rutas estáticas de imágenes del producto garantizando que sean 100% fotos del producto real"""
        galeria = [self.imagen]
        adicionales = list(self.imagenes_galeria.all().order_by('orden').values_list('imagen', flat=True))
        for img in adicionales:
            if img and img not in galeria:
                galeria.append(img)
        return galeria

    def es_360(self):
        """Determina si el producto posee una secuencia de ángulos tipo StockX"""
        gal = self.get_galeria()
        return len(gal) >= 4 or any('angulo' in img.lower() for img in gal)

    def galeria_json(self):
        import json
        return json.dumps(self.get_galeria())

    def imagen_secundaria(self):
        """Devuelve una imagen secundaria del producto para el efecto hover interactivo en el catálogo"""
        adicionales = list(self.imagenes_galeria.all().order_by('orden').values_list('imagen', flat=True))
        for img in adicionales:
            if img and img != self.imagen:
                return img
        return self.imagen

    def __str__(self):
        return self.nombre


class ProductoTalla(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='producto_tallas')
    talla = models.ForeignKey(Talla, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Talla de Producto"
        verbose_name_plural = "Tallas de Producto"
        unique_together = ('producto', 'talla')

    def __str__(self):
        return f"{self.producto.nombre} — {self.talla.nombre}"


class DetalleProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='detalles')
    texto = models.CharField(max_length=255)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Detalle de Producto"
        verbose_name_plural = "Detalles de Producto"
        ordering = ['orden']

    def __str__(self):
        return f"{self.producto.nombre} — {self.texto[:40]}"


class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes_galeria')
    imagen = models.CharField(max_length=255, help_text="Ruta estática de la foto del producto (ej: img/producto_back.jpg)")
    titulo = models.CharField(max_length=100, default='Vista adicional')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Imagen de Producto"
        verbose_name_plural = "Imágenes de Producto"
        ordering = ['orden']

    def __str__(self):
        return f"{self.producto.nombre} — {self.titulo}"


class PreOrden(models.Model):
    ESTADOS = [
        ('CONFIRMADA', 'Pre-Orden Recibida & Confirmada'),
        ('CONFECCION', 'Confección y Bordado Artesanal'),
        ('CONTROL_CALIDAD', 'Control de Calidad & Autenticación VIP'),
        ('DESPACHO_DHL', 'Despacho Internacional DHL Express'),
        ('EN_ADUANA', 'En Aduana / Hub Local Santiago'),
        ('ENTREGADA', 'Entregada / Disponible para Retiro'),
        ('CANCELADA', 'Orden Cancelada & Stock Restituido'),
    ]

    codigo_orden = models.CharField(max_length=50, unique=True, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='preordenes',
        help_text="Cuenta de cliente asociada de forma permanente"
    )
    nombre_cliente = models.CharField(max_length=150)
    email_cliente = models.EmailField(db_index=True, help_text="Copia de respaldo siempre ligada")
    telefono_cliente = models.CharField(max_length=30, blank=True)
    direccion_entrega = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100, default='Santiago')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='preordenes')
    talla = models.CharField(max_length=20, default='M')
    cantidad = models.PositiveIntegerField(default=1)
    precio_total = models.PositiveIntegerField(help_text="Total en CLP")
    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='CONFIRMADA')
    dhl_tracking = models.CharField(max_length=60, default='DHL-GB-88492019')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_estimada_entrega = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Pre-Orden / Pedido"
        verbose_name_plural = "Pre-Órdenes y Pedidos"
        ordering = ['-fecha_creacion']

    def precio_formateado(self):
        return f"${self.precio_total:,}".replace(',', '.')

    def porcentaje_progreso(self):
        mapa = {
            'CONFIRMADA': 20,
            'CONFECCION': 40,
            'CONTROL_CALIDAD': 60,
            'DESPACHO_DHL': 80,
            'EN_ADUANA': 90,
            'ENTREGADA': 100,
            'CANCELADA': 0,
        }
        return mapa.get(self.estado, 20)

    def cancelar_y_restituir_stock(self):
        """Cancela la orden y restituye automáticamente el stock a la base de datos."""
        if self.estado == 'CANCELADA':
            return False
        from django.db.models import F
        pt = ProductoTalla.objects.filter(producto=self.producto, talla__nombre__iexact=self.talla).first()
        if not pt:
            pt = ProductoTalla.objects.filter(producto=self.producto).first()
        if pt:
            pt.stock = F('stock') + self.cantidad
            pt.save(update_fields=['stock'])
        self.estado = 'CANCELADA'
        self.save(update_fields=['estado'])
        return True

    def __str__(self):
        return f"{self.codigo_orden} — {self.nombre_cliente} ({self.producto.nombre})"


class Pedido(models.Model):
    """
    Modelo permanente de Pedido / Order vinculado a la cuenta del usuario y a su email.
    """
    codigo_pedido = models.CharField(max_length=50, unique=True, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pedidos',
        null=True,
        blank=True,
        help_text="Usuario propietario permanente del pedido"
    )
    email = models.EmailField(db_index=True, help_text="Copia de respaldo siempre ligada")
    nombre_cliente = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100, default='Santiago')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='pedidos_producto')
    talla = models.CharField(max_length=20, default='M')
    cantidad = models.PositiveIntegerField(default=1)
    precio_total = models.PositiveIntegerField(help_text="Total en CLP")
    estado = models.CharField(max_length=30, choices=PreOrden.ESTADOS, default='CONFIRMADA')
    notas = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_estimada_entrega = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Pedido Oficial"
        verbose_name_plural = "Pedidos Oficiales"
        ordering = ['-fecha_creacion']

    def precio_formateado(self):
        return f"${self.precio_total:,}".replace(',', '.')

    def cancelar_y_restituir_stock(self):
        """Cancela el pedido y la preorden asociada, restituyendo stock a la base de datos."""
        preorden = PreOrden.objects.filter(codigo_orden=self.codigo_pedido).first()
        if preorden:
            res = preorden.cancelar_y_restituir_stock()
            self.refresh_from_db()
            return res
        if self.estado == 'CANCELADA':
            return False
        from django.db.models import F
        pt = ProductoTalla.objects.filter(producto=self.producto, talla__nombre__iexact=self.talla).first()
        if not pt:
            pt = ProductoTalla.objects.filter(producto=self.producto).first()
        if pt:
            pt.stock = F('stock') + self.cantidad
            pt.save(update_fields=['stock'])
        self.estado = 'CANCELADA'
        self.save(update_fields=['estado'])
        return True

    def __str__(self):
        return f"Pedido {self.codigo_pedido} - {self.email}"


class Tracker(models.Model):
    """
    Modelo permanente de Tracker / Envío con número de guía y estado en vivo.
    """
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='tracker', null=True, blank=True)
    preorden = models.OneToOneField(PreOrden, on_delete=models.CASCADE, related_name='tracker_rel', null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trackers',
        null=True,
        blank=True
    )
    email = models.EmailField(db_index=True, help_text="Copia de respaldo siempre ligada")
    numero_guia = models.CharField(max_length=60, unique=True, db_index=True)
    courier = models.CharField(max_length=60, default='DHL Express Priority')
    estado_envio = models.CharField(max_length=50, default='En Tránsito Internacional')
    ubicacion_actual = models.CharField(max_length=100, default='Hub Central London W12')
    destino = models.CharField(max_length=100, default='Santiago, Chile')
    porcentaje_avance = models.PositiveSmallIntegerField(default=35)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tracker / Seguimiento"
        verbose_name_plural = "Trackers / Seguimientos"
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"{self.numero_guia} ({self.courier}) - {self.email}"


@receiver(post_save, sender=PreOrden)
def sync_preorden_to_pedido_and_tracker(sender, instance, created, **kwargs):
    """Sincroniza automáticamente cada Pre-Orden con los modelos permanentes de Pedido y Tracker."""
    # 1. Asociar usuario si aún no está asignado pero existe por correo
    if not instance.usuario and instance.email_cliente:
        from django.contrib.auth.models import User
        user = User.objects.filter(email__iexact=instance.email_cliente).first()
        if user:
            instance.usuario = user
            PreOrden.objects.filter(pk=instance.pk).update(usuario=user)

    # 2. Crear o actualizar Pedido oficial permanente
    pedido, _ = Pedido.objects.update_or_create(
        codigo_pedido=instance.codigo_orden,
        defaults={
            'usuario': instance.usuario,
            'email': instance.email_cliente,
            'nombre_cliente': instance.nombre_cliente,
            'telefono': instance.telefono_cliente,
            'direccion': instance.direccion_entrega,
            'ciudad': instance.ciudad,
            'producto': instance.producto,
            'talla': instance.talla,
            'cantidad': instance.cantidad,
            'precio_total': instance.precio_total,
            'estado': instance.estado,
            'notas': instance.notas,
            'fecha_estimada_entrega': instance.fecha_estimada_entrega,
        }
    )

    # 3. Crear o actualizar Tracker permanente
    if instance.dhl_tracking:
        Tracker.objects.update_or_create(
            numero_guia=instance.dhl_tracking,
            defaults={
                'pedido': pedido,
                'preorden': instance,
                'usuario': instance.usuario,
                'email': instance.email_cliente,
                'courier': 'DHL Express Priority',
                'estado_envio': instance.get_estado_display(),
                'destino': f"{instance.ciudad}, Chile",
                'porcentaje_avance': instance.porcentaje_progreso(),
            }
        )


@receiver(post_save, sender=Pedido)
def sync_pedido_to_preorden(sender, instance, created, **kwargs):
    """
    Sincroniza cambios desde Pedido hacia PreOrden para consistencia bidireccional
    cuando un administrador modifica estados o notas desde el Django Admin.
    """
    if kwargs.get('raw', False):
        return
    preorden = PreOrden.objects.filter(codigo_orden=instance.codigo_pedido).first()
    if preorden and (preorden.estado != instance.estado or preorden.notas != instance.notas):
        PreOrden.objects.filter(pk=preorden.pk).update(
            estado=instance.estado,
            notas=instance.notas
        )
        if preorden.dhl_tracking:
            Tracker.objects.filter(preorden=preorden).update(
                estado_envio=instance.get_estado_display(),
                porcentaje_avance=preorden.porcentaje_progreso()
            )


