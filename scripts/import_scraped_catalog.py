import os
import sys
import re
import json
import shutil
import django

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "mi_proyecto"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mi_proyecto.settings")
django.setup()

from django.utils.text import slugify
from catalogo.models import Categoria, Talla, Producto, ProductoTalla, DetalleProducto, ImagenProducto
from locales.models import Local
from django.contrib.auth.models import User

SCRAPED_DIR = r"C:\Users\avalo\Documents\antigravity\test\scraped_catalog"
STATIC_CATALOG_DIR = os.path.join(BASE_DIR, "mi_proyecto", "static", "catalog")

CATEGORY_MAPPING = {
    'Accesorios': 'Accesorios',
    'Calzado_Sneakers': 'Calzado / Sneakers',
    'Camisetas_Tops': 'Camisetas & Tops',
    'Otras_Prendas': 'Coleccionables & Otros',
    'Pantalones_Shorts': 'Pantalones & Shorts',
    'Sudaderas_Abrigos': 'Sudaderas & Abrigos',
}

CLOTHES_SIZES = ['S', 'M', 'L', 'XL', 'XXL']
SNEAKER_SIZES = ['US 7.5', 'US 8', 'US 8.5', 'US 9', 'US 9.5', 'US 10', 'US 10.5', 'US 11', 'US 12']
ACCESSORY_SIZES = ['ONE SIZE']

def parse_descripcion(txt_path):
    info = {
        'nombre': '',
        'categoria': '',
        'precio_usd': 0.0,
        'url_tienda': '',
        'detalles': []
    }
    if not os.path.exists(txt_path):
        return info

    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extract name
    m_name = re.search(r'NOMBRE DEL PRODUCTO:\s*(.+)', content)
    if m_name:
        info['nombre'] = m_name.group(1).strip()

    # Extract category
    m_cat = re.search(r'CATEGORÍA:\s*(.+)', content)
    if m_cat:
        info['categoria'] = m_cat.group(1).strip()

    # Extract price
    m_price = re.search(r'PRECIO REGISTRADO:\s*\$?([0-9,.]+)', content)
    if m_price:
        p_str = m_price.group(1).replace(',', '').strip()
        try:
            info['precio_usd'] = float(p_str)
        except ValueError:
            info['precio_usd'] = 150.0

    # Extract store URL
    m_url = re.search(r'Enlace en tienda:\s*(.+)', content)
    if m_url:
        info['url_tienda'] = m_url.group(1).strip()

    # Extract details
    in_details = False
    for line in content.splitlines():
        line = line.strip()
        if 'DETALLES Y CARACTERÍSTICAS:' in line:
            in_details = True
            continue
        if in_details:
            if line.startswith('='):
                break
            if line.startswith('-') or line.startswith('*'):
                det_text = line.lstrip('-* ').strip()
                if det_text:
                    info['detalles'].append(det_text)

    return info

def run():
    print("=== INICIANDO IMPORTACIÓN DEL CATÁLOGO SCRAPEADO ===")
    
    # 1. Preparar directorio estático destino
    if os.path.exists(STATIC_CATALOG_DIR):
        shutil.rmtree(STATIC_CATALOG_DIR)
    os.makedirs(STATIC_CATALOG_DIR, exist_ok=True)

    # 2. Limpiar base de datos de productos anteriores
    print("Eliminando catálogo anterior y limpiando locales...")
    ImagenProducto.objects.all().delete()
    ProductoTalla.objects.all().delete()
    DetalleProducto.objects.all().delete()
    Producto.objects.all().delete()
    Categoria.objects.all().delete()
    Talla.objects.all().delete()
    Local.objects.all().delete()

    # Crear tallas base
    tallas_dict = {}
    for t_name in CLOTHES_SIZES + SNEAKER_SIZES + ACCESSORY_SIZES:
        talla_obj, _ = Talla.objects.get_or_create(nombre=t_name)
        tallas_dict[t_name] = talla_obj

    # 3. Recorrer carpetas de categorías
    cat_dirs = [d for d in os.listdir(SCRAPED_DIR) if os.path.isdir(os.path.join(SCRAPED_DIR, d))]
    cat_dirs.sort()

    total_importados = 0

    for cat_dir_name in cat_dirs:
        cat_path = os.path.join(SCRAPED_DIR, cat_dir_name)
        cat_display = CATEGORY_MAPPING.get(cat_dir_name, cat_dir_name.replace('_', ' '))
        categoria_obj, _ = Categoria.objects.get_or_create(
            nombre=cat_display,
            defaults={'slug': slugify(cat_display)}
        )

        cat_slug = slugify(cat_dir_name)
        prod_dirs = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
        prod_dirs.sort()

        print(f"\nProcesando categoría: {cat_display} ({len(prod_dirs)} productos)...")

        for prod_folder in prod_dirs:
            p_source_dir = os.path.join(cat_path, prod_folder)
            prod_slug = slugify(prod_folder)[:60]
            target_prod_dir = os.path.join(STATIC_CATALOG_DIR, cat_slug, prod_slug)
            os.makedirs(target_prod_dir, exist_ok=True)

            # Leer descripcion.txt
            txt_path = os.path.join(p_source_dir, "descripcion.txt")
            info = parse_descripcion(txt_path)
            
            prod_title = info['nombre'] or prod_folder
            precio_usd = info['precio_usd']
            if precio_usd <= 0:
                precio_usd = 180.0
            
            # Calcular precio CLP estimado (TC aprox $940)
            precio_clp = int(round(precio_usd * 940, -3)) # Redondeo a miles

            # Buscar imágenes ordenadas
            img_files = [f for f in os.listdir(p_source_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            
            # Ordenar para que imagen_1_principal sea primera, luego imagen_2, etc.
            def img_sort_key(name):
                m = re.search(r'imagen_(\d+)', name)
                if m:
                    return int(m.group(1))
                return 999
            img_files.sort(key=img_sort_key)

            if not img_files:
                continue

            # Copiar imágenes al directorio estático
            copied_static_rel_paths = []
            for img_name in img_files:
                src_file = os.path.join(p_source_dir, img_name)
                # Normalizar nombre de archivo
                clean_img_name = img_name.lower().replace(' ', '_')
                dest_file = os.path.join(target_prod_dir, clean_img_name)
                shutil.copy2(src_file, dest_file)
                rel_path = f"catalog/{cat_slug}/{prod_slug}/{clean_img_name}"
                copied_static_rel_paths.append(rel_path)

            primary_img = copied_static_rel_paths[0]

            # Determinar badge
            badge = 'DISPONIBLE'
            if 'travis' in prod_title.lower() or '2026' in prod_title.lower() or 'friends & family' in prod_title.lower():
                badge = 'LIMITED DROP'

            # Subtítulo de marca / estilo
            subtitulo = "Official Drop Archive"
            if "Trapstar" in prod_title:
                subtitulo = "Trapstar London Collection"
            elif "Syna" in prod_title or "Central Cee" in prod_title:
                subtitulo = "Central Cee × Syna World"
            elif "Jordan" in prod_title:
                subtitulo = "Jordan Retro OG Collection"
            elif "Nike" in prod_title:
                subtitulo = "Nike Sportswear Archive"

            # Descripción completa
            descripcion = (
                f"Pieza oficial de archivo: {prod_title}. "
                f"Diseño icónico con materiales de alta densidad y autenticidad certificada. "
                f"Importado y disponible en el catálogo exclusivo de Solariluxury."
            )

            # Crear producto
            prod_obj = Producto.objects.create(
                nombre=prod_title,
                subtitulo=subtitulo,
                precio=precio_clp,
                precio_usd=precio_usd,
                descripcion=descripcion,
                imagen=primary_img,
                badge_estado=badge,
                categoria=categoria_obj
            )

            # Agregar imágenes adicionales a ImagenProducto
            for idx, img_rel in enumerate(copied_static_rel_paths[1:], start=1):
                # Título descriptivo según nombre
                titulo = f"Ángulo {idx}"
                if "angulo" in img_rel:
                    titulo = f"Perspectiva 360° ({idx})"
                elif "reverso" in img_rel:
                    titulo = "Vista posterior / Reverso"
                elif "detalle" in img_rel:
                    titulo = "Detalle de confección"

                ImagenProducto.objects.create(
                    producto=prod_obj,
                    imagen=img_rel,
                    titulo=titulo,
                    orden=idx
                )

            # Asignar tallas correspondientes
            if cat_dir_name == 'Calzado_Sneakers':
                sizes_to_assign = SNEAKER_SIZES
            elif cat_dir_name == 'Accesorios':
                sizes_to_assign = ACCESSORY_SIZES
            else:
                sizes_to_assign = CLOTHES_SIZES

            for s_name in sizes_to_assign:
                t_obj = tallas_dict.get(s_name)
                if t_obj:
                    ProductoTalla.objects.create(producto=prod_obj, talla=t_obj, stock=5)

            # Detalles técnicos
            detalles_base = [
                "100% Autenticidad verificada por Solariluxury",
                f"Categoría oficial: {cat_display}",
                f"Precio internacional de referencia: ${precio_usd:.2f} USD",
                "Packaging y etiquetas originales de drop garantizadas",
                "Envío asegurado con número de seguimiento en tiempo real"
            ]
            if len(copied_static_rel_paths) >= 9:
                detalles_base.insert(0, "Visor 360° interactivo con múltiples ángulos de rotación completa")

            for ord_idx, d_text in enumerate(detalles_base):
                DetalleProducto.objects.create(
                    producto=prod_obj,
                    texto=d_text,
                    orden=ord_idx
                )

            total_importados += 1

    print(f"\n[ÉXITO] ¡Total de productos importados a la base de datos: {total_importados}!")
    print(f"Total Categorías: {Categoria.objects.count()}")
    print(f"Total Imágenes adicionales: {ImagenProducto.objects.count()}")

if __name__ == '__main__':
    run()
