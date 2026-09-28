import os
import sys
import shutil
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "mi_proyecto"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mi_proyecto.settings")

import django
django.setup()

from django.test import Client

client = Client()
DOCS_DIR = os.path.join(BASE_DIR, "docs")

if os.path.exists(DOCS_DIR):
    shutil.rmtree(DOCS_DIR)
os.makedirs(DOCS_DIR, exist_ok=True)

# Copiar estáticos a docs/static
static_src = os.path.join(BASE_DIR, "mi_proyecto", "static")
static_dest = os.path.join(DOCS_DIR, "static")
shutil.copytree(static_src, static_dest, dirs_exist_ok=True)

from catalogo.models import Producto

# Get product IDs from database
producto_ids = list(Producto.objects.values_list('id', flat=True))

# (route, out_path, relative_prefix)
routes = [
    ("/", os.path.join(DOCS_DIR, "index.html"), "./"),
    ("/productos/", os.path.join(DOCS_DIR, "productos", "index.html"), "../"),
    ("/locales/", os.path.join(DOCS_DIR, "locales", "index.html"), "../"),
    ("/locales/informacion/", os.path.join(DOCS_DIR, "locales", "informacion", "index.html"), "../../"),
    ("/login/", os.path.join(DOCS_DIR, "login", "index.html"), "../"),
    ("/registro/", os.path.join(DOCS_DIR, "registro", "index.html"), "../"),
]

for p_id in producto_ids:
    routes.append((f"/productos/{p_id}/", os.path.join(DOCS_DIR, "productos", str(p_id), "index.html"), "../../"))


for route, out_path, rel in routes:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    response = client.get(route)
    if response.status_code == 200:
        html = response.content.decode("utf-8")
        
        # Reemplazar enlaces y recursos con rutas relativas portátiles (doble y simple comilla)
        html = html.replace('href="/static/', f'href="{rel}static/')
        html = html.replace("href='/static/", f"href='{rel}static/")
        html = html.replace('src="/static/', f'src="{rel}static/')
        html = html.replace("src='/static/", f"src='{rel}static/")
        html = html.replace("url('/static/", f"url('{rel}static/")
        html = html.replace("='/static/", f"='{rel}static/")
        html = html.replace('="/static/', f'="{rel}static/')
        html = html.replace('"/static/', f'"{rel}static/')
        html = html.replace("'/static/", f"'{rel}static/")
        html = html.replace("|/static/", f"|{rel}static/")
        
        # Enlaces de navegación interna
        html = html.replace('href="/productos/"', f'href="{rel}productos/"')
        html = html.replace('href="/locales/"', f'href="{rel}locales/"')
        html = html.replace('href="/locales/informacion/"', f'href="{rel}locales/informacion/"')
        html = html.replace('href="/login/"', f'href="{rel}login/"')
        html = html.replace('href="/registro/"', f'href="{rel}registro/"')
        html = html.replace('href="/logout/"', f'href="{rel}index.html"')
        html = html.replace('href="/"', f'href="{rel}index.html"')
        
        # Enlaces a productos individuales
        for pid in producto_ids:
            html = html.replace(f'href="/productos/{pid}/"', f'href="{rel}productos/{pid}/"')
            html = html.replace(f'"url": "/productos/{pid}/"', f'"url": "{rel}productos/{pid}/"')
            html = html.replace(f"window.location.href='/productos/{pid}/'", f"window.location.href='{rel}productos/{pid}/'")
            html = html.replace(f"window.location.href = '/productos/{pid}/'", f"window.location.href = '{rel}productos/{pid}/'")
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Exportado ({rel}): {route} -> {out_path}")
    else:
        print(f"Error {response.status_code} en {route}")

# Crear .nojekyll
with open(os.path.join(DOCS_DIR, ".nojekyll"), "w", encoding="utf-8") as f:
    f.write("")

print("[OK] Exportación estática 100% portable y completa en docs/")
