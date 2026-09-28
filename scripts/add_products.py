import json
import os

def add_products():
    path = 'mi_proyecto/data/productos.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_prods = [
        {
            'id': 15,
            'nombre': 'NIKE DUNK LOW RETRO "WHITE BLACK PANDA"',
            'subtitulo': 'SILUETA CLÁSICA SKATEBOARDING',
            'precio': 129990,
            'precio_usd': '135.00',
            'categoria': 'ZAPATILLAS (SNEAKERS)',
            'descripcion': 'El icónico modelo Dunk Low en su variante más versátil Black & White. Imprescindible para el día a día.',
            'detalles': ['CUERO PREMIUM BLANCO Y NEGRO', 'SUELA DE GOMA DE MÁXIMA TRACCIÓN', 'PERFIL BAJO (LOW TOP)', 'CÓDIGO: DD1391-100'],
            'badge_estado': 'DISPONIBLE',
            'tallas': ['US 8', 'US 9', 'US 10', 'US 11'],
            'imagen': 'img/dunk_panda.jpg'
        },
        {
            'id': 16,
            'nombre': 'TRAPSTAR CAMO HOODIE "STREET EDITION"',
            'subtitulo': 'POLERÓN CAMUFLADO OVERSIZED',
            'precio': 85990,
            'precio_usd': '90.00',
            'categoria': 'POLERONES (HOODIES)',
            'descripcion': 'Polerón grueso con diseño camuflado táctico urbano y logo Trapstar bordado en hilo reforzado.',
            'detalles': ['100% ALGODÓN RÚSTICO DE ALTO GRAMAJE', 'CORTE OVERSIZED', 'CAPUCHA DE DOBLE CAPA', 'BORDADO DE ALTA DENSIDAD'],
            'badge_estado': 'DISPONIBLE',
            'tallas': ['S', 'M', 'L', 'XL'],
            'imagen': 'img/camo_hoodie.jpg'
        }
    ]
    data.extend(new_prods)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print('Added 2 products.')

if __name__ == '__main__':
    add_products()
