from django.db import models

class Local(models.Model):
    TIPO_CHOICES = [
        ('FLAGSHIP', 'Flagship Store'),
        ('SHOWROOM', 'Showroom'),
        ('POP_UP', 'Pop-Up'),
    ]

    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=300)
    horario = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    imagen = models.CharField(max_length=255, default='img/local1.jpg')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='FLAGSHIP')
    activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Local / Tienda"
        verbose_name_plural = "Locales / Tiendas"
        ordering = ['nombre']

    def badge_tipo(self):
        return f"SOLARY {self.tipo}"

    def __str__(self):
        return self.nombre
