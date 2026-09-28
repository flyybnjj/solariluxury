import json
import random
import secrets
import logging
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.models import User
from usuarios.models import Cliente
from .models import Producto, Categoria, DetalleProducto, ImagenProducto, PreOrden, Pedido, Tracker

logger = logging.getLogger(__name__)


def inicio(request):
    """
    SOLARILUXURY x CENTRAL CEE — Official Interactive Campaign Experience
    Data served from database via Django ORM.
    """
    productos = list(
        Producto.objects.select_related('categoria')
        .prefetch_related('tallas', 'detalles', 'imagenes_galeria')
        .all()
    )

    # Format prices and prepare gallery
    for p in productos:
        p.precio_fmt = f"${p.precio:,}".replace(',', '.')
        p.galeria_list = p.get_galeria()
        p.hover_img = p.imagen_secundaria()
        p.es_360_val = p.es_360()
        p.galeria_json_val = p.galeria_json()

    # Curated Bestseller / Star Products for the Dynamic Rotating Showcase
    bestseller_ids = [49, 46, 76, 35, 44]  # AF1 Syna, Jordan 4 Toro Bravo, Tech Fleece, Swatch AP, Jordan 1 Travis
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


@csrf_exempt
def solicitar_key(request):
    """
    Genera un PIN de 6 dígitos único y despacha el correo mediante Gmail SMTP real con fail_silently=False.
    NUNCA devuelve el PIN al navegador en la respuesta.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email', '').strip().lower()
    except Exception:
        email = request.POST.get('email', '').strip().lower()

    if not email or '@' not in email:
        return JsonResponse({'success': False, 'error': 'Por favor ingresa un correo electrónico válido.'}, status=400)

    # 1. Obtener o auto-crear usuario en Django
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        base_username = email.split('@')[0].replace('.', '_').replace('-', '_')
        username = base_username
        c = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{c}"
            c += 1
        user = User.objects.create_user(username=username, email=email)
        user.set_unusable_password()
        user.save()

    cliente, _ = Cliente.objects.get_or_create(user=user)

    # 2. Generar PIN numérico de 6 dígitos único con validez de 10 minutos (criptográficamente seguro)
    pin = f"{secrets.randbelow(900000) + 100000}"
    cliente.access_pin = pin
    cliente.pin_expires_at = timezone.now() + timedelta(minutes=10)
    cliente.save()

    user.access_pin = pin
    user.pin_expires_at = cliente.pin_expires_at
    user.save()

    # Guardar en sesión el correo para validación
    request.session['auth_otp_email'] = email

    # 3. Envío 100% REAL mediante Gmail SMTP obligatorio
    pin_spaced = f"{pin[:3]}   {pin[3:]}"
    cliente_nombre = user.get_full_name() or user.first_name or "Test Test"
    html_message = render_to_string('usuarios/email_pin_acceso.html', {
        'pin': pin,
        'pin_spaced': pin_spaced,
        'cliente_nombre': cliente_nombre,
        'user': user,
        'email': email,
    })
    plain_message = f"Tu código de verificación de Solary es: {pin}\nVálido durante 10 minutos."

    try:
        send_mail(
            subject=f"Tu código de verificación de Solary: {pin}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
    except Exception as e:
        logger.error(f"[ERROR SMTP GMAIL] Falló el despacho de correo: {e}")
        return JsonResponse({
            'success': False,
            'error': f"Error al enviar correo por Gmail SMTP ({e}). Revisa tus credenciales en el archivo .env."
        }, status=500)

    return JsonResponse({
        'success': True,
        'email': email,
        'message': 'Hemos enviado un código PIN de 6 dígitos a tu correo. Revisa tu bandeja de entrada o spam e ingrésalo abajo.'
    })


@csrf_exempt
def validar_key(request):
    """
    Valida el PIN de 6 dígitos recibido por correo.
    - Quema el PIN inmediatamente para que sea de un solo uso.
    - Inicia sesión del usuario en Django.
    - Desbloquea la tienda y vincula pedidos y trackers.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email', '').strip().lower() or request.session.get('auth_otp_email', '')
        pin = data.get('pin', '') or data.get('key', '')
        pin = str(pin).strip()
    except Exception:
        email = request.POST.get('email', '').strip().lower() or request.session.get('auth_otp_email', '')
        pin = str(request.POST.get('pin', '') or request.POST.get('key', '')).strip()

    if not email:
        return JsonResponse({'success': False, 'error': 'No se encontró la dirección de correo electrónico.'}, status=400)
    if not pin or len(pin) != 6 or not pin.isdigit():
        return JsonResponse({'success': False, 'error': 'Debes ingresar el PIN numérico de 6 dígitos recibido por correo.'}, status=400)

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return JsonResponse({'success': False, 'error': 'Usuario no registrado con este correo.'}, status=404)

    cliente, _ = Cliente.objects.get_or_create(user=user)

    if cliente.esta_bloqueado():
        return JsonResponse({
            'success': False,
            'error': 'Demasiados intentos fallidos. Tu acceso ha sido bloqueado temporalmente por 15 minutos.'
        }, status=429)

    if not cliente.access_pin or not cliente.pin_expires_at:
        return JsonResponse({'success': False, 'error': 'El PIN no es válido o ya fue utilizado. Solicita uno nuevo.'}, status=400)

    if timezone.now() > cliente.pin_expires_at:
        cliente.clear_pin()
        return JsonResponse({'success': False, 'error': 'El código PIN ha caducado (10 minutos de validez). Solicita uno nuevo.'}, status=400)

    if not secrets.compare_digest(str(cliente.access_pin).strip(), pin):
        cliente.intentos_fallidos += 1
        if cliente.intentos_fallidos >= 5:
            cliente.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
            cliente.clear_pin()
            cliente.save()
            return JsonResponse({
                'success': False,
                'error': 'Has superado el límite de 5 intentos fallidos. Tu acceso ha sido bloqueado por 15 minutos y el código PIN ha sido invalidado.'
            }, status=429)
        cliente.save()
        return JsonResponse({
            'success': False,
            'error': f'El código PIN ingresado es incorrecto. Te quedan {5 - cliente.intentos_fallidos} intentos.'
        }, status=400)

    # 1. QUEMAR EL PIN INMEDIATAMENTE Y RESETEAR INTENTOS
    cliente.intentos_fallidos = 0
    cliente.bloqueado_hasta = None
    cliente.clear_pin()
    user.access_pin = None
    user.pin_expires_at = None
    user.save()

    # 2. INICIAR SESIÓN REAL
    login(request, user)
    request.session['tienda_desbloqueada'] = True
    request.session['vip_unlocked_email'] = email

    # Enviar cupón de bienvenida exclusivamente en el primer login
    try:
        from usuarios.utils import enviar_cupon_bienvenida
        enviar_cupon_bienvenida(user, email=email)
    except Exception as e:
        logger.error(f"[ERROR CUPON BIENVENIDA] {e}")

    # 3. Vincular permanentemente pedidos y trackers
    PreOrden.objects.filter(email_cliente__iexact=email, usuario__isnull=True).update(usuario=user)
    Pedido.objects.filter(email__iexact=email, usuario__isnull=True).update(usuario=user)
    Tracker.objects.filter(email__iexact=email, usuario__isnull=True).update(usuario=user)

    return JsonResponse({
        'success': True,
        'message': f'¡Acceso concedido! Bienvenido/a {user.first_name or user.username}. Desbloqueando tienda...'
    })


def bloquear_tienda(request):
    """Vuelve a bloquear la tienda y regresa al portal privado / gateway"""
    from django.contrib.auth import logout
    logout(request)
    request.session.flush()
    return redirect('inicio')


def lista_productos(request):
    """Catálogo oficial Solariluxury con filtros interactivos, ordenamiento y vistas dinámicas"""
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


def detalle_producto(request, producto_id):
    """Detalle interactivo del producto con galería 100% de producto real y selector de tallas"""
    producto = get_object_or_404(
        Producto.objects.select_related('categoria')
        .prefetch_related('tallas', 'detalles', 'imagenes_galeria'),
        id=producto_id
    )
    producto.precio_fmt = f"${producto.precio:,}".replace(',', '.')

    tallas = list(producto.tallas.all())
    detalles = list(producto.detalles.all())
    galeria = producto.get_galeria()

    # Productos relacionados (mismo estilo o categoría)
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

    # Previous / Next navigation
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

