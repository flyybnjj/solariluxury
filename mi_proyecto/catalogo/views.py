import json
import random
import secrets
import logging
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from usuarios.models import Cliente
from .models import Producto, Categoria, DetalleProducto, ImagenProducto, PreOrden, Pedido, Tracker

logger = logging.getLogger(__name__)

@never_cache
@login_required(login_url='login')
def inicio(request):
    productos = list(
        Producto.objects.select_related('categoria')
        .prefetch_related('tallas', 'detalles', 'imagenes_galeria')
        .all()
    )

    for p in productos:
        p.precio_fmt = f"${p.precio:,}".replace(',', '.')
        p.galeria_list = p.get_galeria()
        p.hover_img = p.imagen_secundaria()
        p.es_360_val = p.es_360()
        p.galeria_json_val = p.galeria_json()

    bestseller_ids = [49, 46, 76, 35, 44]
    bestseller_qs = [p for p in productos if p.id in bestseller_ids]
    if len(bestseller_qs) < 4:
        bestseller_qs = productos[:5]

    bestsellers_data = []
    badges = [
        ("PRODUCTO MÁS VENDIDO #1", "342 unidades vendidas en las últimas 24h", "TOP VENTAS MUNDIAL", "flame"),
        ("PRODUCTO ESTRELLA DEL DROP", "Stock restante: 6 unidades en bodega", "PIEZA MAESTRA 2026", "star"),
        ("DROP MÁS COTIZADO DEL MES", "Más de 500 solicitudes en lista de espera", "EDICIÓN LIMITADA", "diamond"),
        ("TENDENCIA VIRAL EN LONDRES", "Alta demanda confirmada en Shepherd's Bush", "SELECCIÓN OFICIAL", "bolt"),
        ("PIEZA ICÓNICA ARCHIVE", "Certificado de autenticidad y entrega inmediata", "EXCLUSIVO SOLARILUXURY", "trophy"),
    ]

    for idx, p in enumerate(bestseller_qs):
        badge_title, live_counter, tag_label, icon_type = badges[idx % len(badges)]
        specs = [d.texto for d in p.detalles.all()[:5]]
        if not specs:
            specs = [
                "PIEZA OFICIAL CAMPAÑA AUTUMN/WINTER 2026",
                "MATERIALES DE ALTA COSTURA STREETWEAR",
                "CERTIFICADO DE AUTENTICIDAD INCLUIDO",
                "ENVÍO INTERNACIONAL EXPRESS",
                "EDICIÓN LIMITADA NUMERADA"
            ]
        bestsellers_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'subtitulo': p.subtitulo or 'CAMPAÑA OFICIAL SOLARILUXURY 2026',
            'categoria': p.categoria.nombre if p.categoria else 'STREETWEAR',
            'imagen': f"/static/{p.imagen}",
            'precio_fmt': str(p.precio_fmt),
            'precio_usd': str(p.precio_usd),
            'badge_title': badge_title,
            'live_counter': live_counter,
            'tag_label': tag_label,
            'icon_type': icon_type,
            'specs': specs,
            'url': f"/productos/{p.id}/",
        })

    hero_prod = bestseller_qs[0] if bestseller_qs else (productos[0] if productos else None)

    categorias = list(Categoria.objects.all().values_list('nombre', flat=True))
    categorias = ['TODOS'] + categorias

    tienda_desbloqueada = request.session.get('tienda_desbloqueada', False) or request.user.is_authenticated

    context = {
        'productos': productos,
        'hero_prod': hero_prod,
        'bestsellers_data': bestsellers_data,
        'bestsellers_json': json.dumps(bestsellers_data, default=str),
        'categorias': categorias,
        'total_productos': len(productos),
        'tienda_desbloqueada': tienda_desbloqueada,
        'vip_unlocked_email': request.session.get('vip_unlocked_email', ''),
    }
    return render(request, 'catalogo/inicio.html', context)

def bloquear_tienda(request):
    from django.contrib.auth import logout
    logout(request)
    request.session.flush()
    return redirect('inicio')

@never_cache
@login_required(login_url='login')
def lista_productos(request):
    categoria_seleccionada = request.GET.get('categoria', 'TODOS').upper()
    busqueda = request.GET.get('q', '').strip()

    productos_qs = (
        Producto.objects.select_related('categoria')
        .prefetch_related('tallas', 'detalles', 'imagenes_galeria')
        .all()
    )

    if busqueda:
        productos_qs = productos_qs.filter(nombre__icontains=busqueda)

    if categoria_seleccionada and categoria_seleccionada != 'TODOS':
        productos_qs = productos_qs.filter(categoria__nombre__iexact=categoria_seleccionada)

    productos = list(productos_qs)
    for p in productos:
        p.precio_fmt = f"${p.precio:,}".replace(',', '.')
        p.galeria_list = p.get_galeria()
        p.hover_img = p.imagen_secundaria()
        p.es_360_val = p.es_360()
        p.galeria_json_val = p.galeria_json()

    categorias = ['TODOS'] + list(Categoria.objects.all().values_list('nombre', flat=True))

    context = {
        'productos': productos,
        'total_productos': len(productos),
        'categorias': categorias,
        'categoria_actual': categoria_seleccionada,
        'busqueda': busqueda,
    }
    return render(request, 'catalogo/productos.html', context)

@never_cache
@login_required(login_url='login')
def detalle_producto(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria')
        .prefetch_related('tallas', 'detalles', 'imagenes_galeria'),
        id=producto_id
    )
    producto.precio_fmt = f"${producto.precio:,}".replace(',', '.')

    tallas = list(producto.tallas.all())
    detalles = list(producto.detalles.all())
    galeria = producto.get_galeria()

    relacionados = list(
        Producto.objects.filter(categoria=producto.categoria)
        .exclude(id=producto.id)
        .select_related('categoria')
        .prefetch_related('imagenes_galeria')[:4]
    )
    if len(relacionados) < 4:
        extra_ids = [p.id for p in relacionados] + [producto.id]
        extras = list(
            Producto.objects.exclude(id__in=extra_ids)
            .select_related('categoria')
            .prefetch_related('imagenes_galeria')[: 4 - len(relacionados)]
        )
        relacionados.extend(extras)

    for r in relacionados:
        r.precio_fmt = f"${r.precio:,}".replace(',', '.')
        r.hover_img = r.imagen_secundaria()
        r.es_360_val = r.es_360()
        r.galeria_json_val = r.galeria_json()

    ids = list(Producto.objects.values_list('id', flat=True).order_by('id'))
    curr_idx = ids.index(producto_id)
    prev_id = ids[curr_idx - 1] if curr_idx > 0 else ids[-1]
    next_id = ids[curr_idx + 1] if curr_idx < len(ids) - 1 else ids[0]

    context = {
        'prod': producto,
        'tallas': tallas,
        'detalles': detalles,
        'galeria': galeria,
        'es_360': producto.es_360(),
        'galeria_json': producto.galeria_json(),
        'relacionados': relacionados,
        'prev_id': prev_id,
        'next_id': next_id,
    }
    return render(request, 'catalogo/detalle_producto.html', context)

from .models import Talla

def _staff_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect as _redirect
            return _redirect('/solicitar-acceso/?next=' + request.path)
        if not (request.user.is_staff or request.user.is_superuser):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Acceso denegado - Solo administradores.')
        return view_func(request, *args, **kwargs)
    return wrapper

@_staff_required
def admin_productos(request):
    q = request.GET.get('q', '').strip()
    cat_id = request.GET.get('categoria', '')
    productos_qs = Producto.objects.select_related('categoria').prefetch_related('tallas').order_by('id')
    if q:
        productos_qs = productos_qs.filter(nombre__icontains=q)
    if cat_id:
        productos_qs = productos_qs.filter(categoria_id=cat_id)
    categorias = Categoria.objects.all()
    context = {
        'productos': productos_qs,
        'categorias': categorias,
        'q': q,
        'cat_id': cat_id,
        'total': productos_qs.count(),
    }
    return render(request, 'catalogo/admin_productos.html', context)

@_staff_required
def admin_crear_producto(request):
    categorias = Categoria.objects.all()
    tallas = Talla.objects.all()
    error = None
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            if not nombre:
                raise ValueError('El nombre es obligatorio.')
            precio_raw = request.POST.get('precio', '0').replace('.', '').replace(',', '').strip()
            precio = int(precio_raw) if precio_raw.isdigit() else 0
            prod = Producto.objects.create(
                nombre=nombre,
                subtitulo=request.POST.get('subtitulo', '').strip(),
                precio=precio,
                precio_usd=request.POST.get('precio_usd', 0) or 0,
                descripcion=request.POST.get('descripcion', '').strip(),
                imagen=request.POST.get('imagen', 'img/placeholder.jpg').strip() or 'img/placeholder.jpg',
                codigo_estilo=request.POST.get('codigo_estilo', '').strip() or None,
                color=request.POST.get('color', '').strip() or None,
                badge_estado=request.POST.get('badge_estado', 'DISPONIBLE'),
                categoria_id=request.POST.get('categoria') or None,
            )
            from .models import ProductoTalla
            talla_ids = request.POST.getlist('tallas')
            for tid in talla_ids:
                sv = request.POST.get('stock_' + str(tid), '1') or '1'
                stock = int(sv) if sv.isdigit() else 1
                ProductoTalla.objects.get_or_create(
                    producto=prod, talla_id=int(tid), defaults={'stock': stock}
                )
            messages.success(request, 'Producto ' + nombre + ' creado exitosamente (ID: ' + str(prod.id) + ').')
            return redirect('admin_productos')
        except Exception as exc:
            error = str(exc)
    return render(request, 'catalogo/admin_crear_producto.html', {
        'categorias': categorias,
        'tallas': tallas,
        'error': error,
        'badge_choices': Producto.BADGE_CHOICES,
    })

@_staff_required
def admin_editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    categorias = Categoria.objects.all()
    tallas = Talla.objects.all()
    from .models import ProductoTalla
    tallas_actuales = {pt.talla_id: pt.stock for pt in ProductoTalla.objects.filter(producto=producto)}
    error = None
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            if not nombre:
                raise ValueError('El nombre es obligatorio.')
            precio_raw = request.POST.get('precio', '0').replace('.', '').replace(',', '').strip()
            precio = int(precio_raw) if precio_raw.isdigit() else producto.precio
            producto.nombre = nombre
            producto.subtitulo = request.POST.get('subtitulo', '').strip()
            producto.precio = precio
            usd_raw = request.POST.get('precio_usd', '').replace(',', '.').strip()
            if usd_raw:
                try:
                    producto.precio_usd = float(usd_raw)
                except ValueError:
                    pass
            producto.descripcion = request.POST.get('descripcion', '').strip()
            imagen = request.POST.get('imagen', '').strip()
            if imagen:
                producto.imagen = imagen
            producto.codigo_estilo = request.POST.get('codigo_estilo', '').strip() or None
            producto.color = request.POST.get('color', '').strip() or None
            producto.badge_estado = request.POST.get('badge_estado', producto.badge_estado)
            cat_id = request.POST.get('categoria')
            producto.categoria_id = int(cat_id) if cat_id else None
            producto.save()
            talla_ids = request.POST.getlist('tallas')
            talla_ids_int = [int(t) for t in talla_ids if t.isdigit()]
            ProductoTalla.objects.filter(producto=producto).exclude(talla_id__in=talla_ids_int).delete()
            for tid in talla_ids_int:
                sv = request.POST.get('stock_' + str(tid), '1') or '1'
                stock = int(sv) if sv.isdigit() else 1
                pt, created = ProductoTalla.objects.get_or_create(
                    producto=producto, talla_id=tid, defaults={'stock': stock}
                )
                if not created:
                    pt.stock = stock
                    pt.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('admin_productos')
        except Exception as exc:
            error = str(exc)
    return render(request, 'catalogo/admin_editar_producto.html', {
        'producto': producto,
        'categorias': categorias,
        'tallas': tallas,
        'tallas_actuales': tallas_actuales,
        'error': error,
        'badge_choices': Producto.BADGE_CHOICES,
    })

@_staff_required
def admin_eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        nombre = producto.nombre
        try:
            producto.delete()
            messages.success(request, 'Producto «' + nombre + '» eliminado exitosamente.')
        except Exception:
            producto.badge_estado = 'AGOTADO'
            producto.save()
            messages.warning(request, 'El producto «' + nombre + '» tiene pedidos registrados y no puede ser borrado físicamente; ha sido marcado como AGOTADO.')
        return redirect('admin_productos')
    return render(request, 'catalogo/admin_confirmar_eliminar.html', {'producto': producto})
