from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente')
    access_pin = models.CharField(
        max_length=6, 
        blank=True, 
        null=True, 
        verbose_name="PIN de Acceso (OTP)"
    )
    pin_expires_at = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Expiración del PIN"
    )
    ha_recibido_cupon = models.BooleanField(
        default=False,
        verbose_name="Cupón de Bienvenida Enviado"
    )
    cupon_bienvenida_codigo = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name="Código de Cupón Único de Bienvenida"
    )

    class Meta:
        verbose_name = "Cliente / Perfil OTP"
        verbose_name_plural = "Clientes / Perfiles OTP"

    def __str__(self):
        return f"Cliente {self.user.email or self.user.username}"

    def is_pin_valid(self, candidate_pin):
        """Verifica si el PIN es correcto y si aún no ha expirado."""
        if not self.access_pin or not self.pin_expires_at:
            return False
        if timezone.now() > self.pin_expires_at:
            return False
        return str(self.access_pin).strip() == str(candidate_pin).strip()

    def clear_pin(self):
        """Invalida el PIN inmediatamente tras su uso exitoso."""
        self.access_pin = None
        self.pin_expires_at = None
        self.save(update_fields=['access_pin', 'pin_expires_at'])


@receiver(post_save, sender=User)
def ensure_cliente_profile(sender, instance, created, **kwargs):
    """Garantiza que todo usuario en el sistema tenga su perfil de cliente asociado con un código de cupón único."""
    if created:
        cliente, _ = Cliente.objects.get_or_create(user=instance)
        if not cliente.cupon_bienvenida_codigo:
            from .utils import generar_codigo_cupon_unico
            cliente.cupon_bienvenida_codigo = generar_codigo_cupon_unico(instance)
            cliente.save(update_fields=['cupon_bienvenida_codigo'])
    else:
        if hasattr(instance, 'cliente'):
            instance.cliente.save()


# Helper properties directly on User so user.access_pin and user.pin_expires_at work smoothly
User.add_to_class('access_pin', property(
    lambda self: getattr(getattr(self, 'cliente', None), 'access_pin', None),
    lambda self, val: setattr(self.cliente, 'access_pin', val) if hasattr(self, 'cliente') else None
))
User.add_to_class('pin_expires_at', property(
    lambda self: getattr(getattr(self, 'cliente', None), 'pin_expires_at', None),
    lambda self, val: setattr(self.cliente, 'pin_expires_at', val) if hasattr(self, 'cliente') else None
))


class TicketSoporte(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código de Ticket")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Solicitante")
    email = models.EmailField(verbose_name="Email de la cuenta SOLARY ID")
    contacto_alternativo = models.CharField(max_length=150, blank=True, verbose_name="WhatsApp o Contacto Alternativo")
    motivo = models.CharField(max_length=255, verbose_name="Motivo del Problema")
    mensaje = models.TextField(verbose_name="Detalle de la solicitud")
    estado = models.CharField(
        max_length=20,
        choices=[
            ('ABIERTO', 'Abierto'),
            ('EN_REVISION', 'En Revisión'),
            ('RESUELTO', 'Resuelto')
        ],
        default='ABIERTO'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket de Soporte"
        verbose_name_plural = "Tickets de Soporte"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.codigo} - {self.email} ({self.estado})"
