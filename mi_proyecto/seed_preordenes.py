import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from catalogo.models import Producto, PreOrden

p1 = Producto.objects.filter(nombre__icontains='jordan').first() or Producto.objects.first()
p2 = Producto.objects.filter(nombre__icontains='swatch').first() or Producto.objects.first()
p3 = Producto.objects.filter(nombre__icontains='syna').first() or Producto.objects.last()

orders = [
    {
        'codigo': 'TP-2026-0492',
        'cliente': 'Central Cee VIP Member',
        'email': 'vip@solariluxury.com',
        'tel': '+56 9 9123 4567',
        'dir': 'Alonso de Córdova 3890, Depto 1402',
        'ciudad': 'Vitacura, Santiago',
        'prod': p1,
        'talla': '42.5 EU / 9 US',
        'precio': p1.precio,
        'estado': 'DESPACHO_DHL',
        'dhl': 'DHL-GB-88492019',
        'fecha_est': date.today() + timedelta(days=5),
        'notas': 'Edición especial Drop 01 con certificado Chenille firmado.'
    },
    {
        'codigo': 'SL-2026-0001',
        'cliente': 'Ignacio Avalos',
        'email': 'avalo@solariluxury.com',
        'tel': '+56 9 8765 4321',
        'dir': 'Av. El Golf 40, Piso 18',
        'ciudad': 'Las Condes, Santiago',
        'prod': p2,
        'talla': 'Única (41mm)',
        'precio': p2.precio,
        'estado': 'CONTROL_CALIDAD',
        'dhl': 'DHL-CH-44910283',
        'fecha_est': date.today() + timedelta(days=8),
        'notas': 'Reserva Prioritaria VIP Black Tier.'
    },
    {
        'codigo': 'SL-2026-0894',
        'cliente': 'Valentina Rossi',
        'email': 'v.rossi@londonluxury.co.uk',
        'tel': '+44 7700 900123',
        'dir': "12 Shepherd's Bush Green",
        'ciudad': 'West London, UK',
        'prod': p3,
        'talla': 'L',
        'precio': p3.precio,
        'estado': 'CONFECCION',
        'dhl': 'DHL-UK-11293847',
        'fecha_est': date.today() + timedelta(days=12),
        'notas': 'Pre-orden campaña Autumn/Winter 2026.'
    }
]

for o in orders:
    obj, created = PreOrden.objects.get_or_create(
        codigo_orden=o['codigo'],
        defaults={
            'nombre_cliente': o['cliente'],
            'email_cliente': o['email'],
            'telefono_cliente': o['tel'],
            'direccion_entrega': o['dir'],
            'ciudad': o['ciudad'],
            'producto': o['prod'],
            'talla': o['talla'],
            'precio_total': o['precio'],
            'estado': o['estado'],
            'dhl_tracking': o['dhl'],
            'fecha_estimada_entrega': o['fecha_est'],
            'notas': o['notas'],
        }
    )
    print(f"Order {o['codigo']}: created={created}")
