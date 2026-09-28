"""
Script para poblar la base de datos desde los archivos JSON existentes.
Ejecutar desde: mi_proyecto/ con el venv activo.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import json
from catalogo.models import Categoria, Talla, Producto, ProductoTalla, DetalleProducto
from locales.models import Local

# Clear existing data
print("Limpiando base de datos...")
ProductoTalla.objects.all().delete()
DetalleProducto.objects.all().delete()
Producto.objects.all().delete()
Talla.objects.all().delete()
Categoria.objects.all().delete()
Local.objects.all().delete()

# Load productos
json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'productos.json')
with open(json_path, 'r', encoding='utf-8-sig') as f:
    productos_data = json.load(f)

print(f"Cargando {len(productos_data)} productos...")

for p in productos_data:
    # Categoria
    cat_nombre = p.get('categoria', 'SIN CATEGORIA')
    categoria, _ = Categoria.objects.get_or_create(nombre=cat_nombre)

    # Producto
    producto = Producto.objects.create(
        nombre=p['nombre'],
        subtitulo=p.get('subtitulo', ''),
        precio=p['precio'],
        precio_usd=p.get('precio_usd', 0),
        descripcion=p.get('descripcion', ''),
        imagen=p.get('imagen', 'img/placeholder.jpg'),
        badge_estado=p.get('badge_estado', 'DISPONIBLE'),
        categoria=categoria,
    )

    # Tallas
    for t_nombre in p.get('tallas', []):
        talla, _ = Talla.objects.get_or_create(nombre=t_nombre)
        ProductoTalla.objects.create(producto=producto, talla=talla, stock=10)

    # Detalles
    for idx, detalle_texto in enumerate(p.get('detalles', [])):
        DetalleProducto.objects.create(
            producto=producto,
            texto=detalle_texto,
            orden=idx
        )

print(f"[OK] {Producto.objects.count()} productos cargados.")
print(f"[OK] {Categoria.objects.count()} categorias creadas.")
print(f"[OK] {Talla.objects.count()} tallas creadas.")
print(f"[OK] {DetalleProducto.objects.count()} detalles creados.")

# Load locales
locales_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'locales.json')
with open(locales_json_path, 'r', encoding='utf-8-sig') as f:
    locales_data = json.load(f)

print(f"\nCargando {len(locales_data)} locales...")
for l in locales_data:
    Local.objects.create(
        nombre=l['nombre'],
        direccion=l['direccion'],
        horario=l['horario'],
        telefono=l['telefono'],
        imagen=l.get('imagen', 'img/local1.jpg'),
        tipo='FLAGSHIP' if 'Mall' in l['nombre'] else 'SHOWROOM',
    )

print(f"[OK] {Local.objects.count()} locales cargados.")

print("\n[DONE] Base de datos poblada exitosamente!")
