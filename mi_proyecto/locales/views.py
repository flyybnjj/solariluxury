import json
import logging
import random
import requests
from datetime import date, timedelta
import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from .models import Local
from catalogo.models import CheckoutRequest, Producto, PreOrden, ProductoTalla

logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    pass

def lista_locales(request):
    locales = Local.objects.filter(activo=True)
    context = {
        'locales': locales,
        'total_locales': locales.count(),
    }
    return render(request, 'locales/lista_locales.html', context)

from django.template.loader import render_to_string

SITE_URL = "http://ec2-32-193-109-160.compute-1.amazonaws.com"

def enviar_correo_preorden(orden):
    fecha_entrega_str = orden.fecha_estimada_entrega.strftime('%d de %B de %Y') if orden.fecha_estimada_entrega else 'Por coordinar'
    tracking_url = f"{SITE_URL}/locales/informacion/?codigo={orden.codigo_orden}"

    total_val = orden.precio_total or (orden.producto.precio * orden.cantidad)
    neto_val = round(total_val / 1.19)
    iva_val = total_val - neto_val

    subtotal_str = f"${total_val:,.0f} CLP".replace(',', '.')
    iva_str = f"${iva_val:,.0f} CLP".replace(',', '.')

    img_rel = orden.producto.imagen.lstrip('/') if orden.producto.imagen else 'img/placeholder.jpg'
    img_abs = f"{SITE_URL}/static/{img_rel}"
    codigo_estilo_val = orden.producto.codigo_estilo or f"SL-{orden.producto.id:04d}"
    color_val = orden.producto.color or "Black Edition"

    prod_dict = {
        'id': orden.producto.id,
        'nombre': orden.producto.nombre,
        'subtitulo': orden.producto.subtitulo or f"{orden.producto.nombre} · {color_val}",
        'imagen_url': img_abs,
        'codigo_estilo': codigo_estilo_val,
        'color': color_val,
        'precio_formateado': orden.producto.precio_formateado(),
    }

    ctx = {
        'orden': orden,
        'pedido_id': orden.codigo_orden,
        'cliente_nombre': orden.nombre_cliente,
        'producto': prod_dict,
        'producto_nombre': orden.producto.nombre,
        'producto_subtitulo': prod_dict['subtitulo'],
        'talla': orden.talla,
        'cantidad': orden.cantidad,
        'estilo': codigo_estilo_val,
        'direccion': orden.direccion_entrega,
        'ciudad': orden.ciudad,
        'comuna': f"{orden.ciudad}, Región Metropolitana" if orden.ciudad else "Santiago",
        'fecha_estimada': fecha_entrega_str,
        'fecha_entrega': fecha_entrega_str,
        'llegada_programada': fecha_entrega_str,
        'guia_dhl': orden.dhl_tracking,
        'total': orden.precio_formateado(),
        'total_precio': subtotal_str,
        'subtotal': subtotal_str,
        'iva': iva_str,
        'tracker_url': tracking_url,
        'dhl_url': f"https://www.dhl.com/cl-es/home/tracking/tracking-express.html?submit=1&tracking-id={orden.dhl_tracking}",
        'detalles_url': tracking_url,
    }

    if orden.estado == 'ENTREGADA':
        asunto = f"SOLARY — Tu pedido ha sido entregado (Orden #{orden.codigo_orden})"
        template = 'emails/email_pedido_entregado.html'
    elif orden.estado in ['DESPACHO_DHL', 'EN_ADUANA']:
        asunto = f"SOLARY — Tu pedido está en camino (Guía DHL #{orden.dhl_tracking})"
        template = 'emails/email_pedido_despachado.html'
    else:
        asunto = f"SOLARY — Estamos preparando tu pedido #{orden.codigo_orden}"
        template = 'emails/email_preparando_pedido.html'

    mensaje_html = render_to_string(template, ctx)
    mensaje_texto = f"SOLARY LUXURY\n{asunto}\nOrden: {orden.codigo_orden}\nSeguimiento: {tracking_url}"

    try:
        send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'vip@solaryluxury.com'),
            recipient_list=[orden.email_cliente],
            html_message=mensaje_html,
            fail_silently=False
        )
        return True
    except Exception as exc:
        logger.error('Purchase receipt email failed (exception=%s)', type(exc).__name__)
        return False


def _existing_order_response(orden):
    return JsonResponse({
        'success': True,
        'codigo_orden': orden.codigo_orden,
        'mensaje': f'Este pedido ya estaba registrado con el código {orden.codigo_orden}.',
        'correo_enviado': None,
        'email': orden.email_cliente,
        'dhl_tracking': orden.dhl_tracking,
        'precio_fmt': orden.precio_formateado(),
        'descuento_aplicado': 0,
        'tracking_url': f"/locales/informacion/?codigo={orden.codigo_orden}",
    })

def get_timeline_para_orden(orden):
    estados_lista = ['CONFIRMADA', 'CONFECCION', 'CONTROL_CALIDAD', 'DESPACHO_DHL', 'EN_ADUANA', 'ENTREGADA']
    idx_actual = estados_lista.index(orden.estado) if orden.estado in estados_lista else 0

    creacion = orden.fecha_creacion.strftime('%d %b %Y')
    f1 = (orden.fecha_creacion + timedelta(days=2)).strftime('%d %b %Y')
    f2 = (orden.fecha_creacion + timedelta(days=5)).strftime('%d %b %Y')
    f3 = orden.fecha_estimada_entrega.strftime('%d %b %Y') if orden.fecha_estimada_entrega else 'Fecha estimada en curso'

    pasos = [
        {
            'titulo': 'CONFECCIÓN Y BORDADO CHENILLE FINALIZADO',
            'sub': f'London Atelier • {creacion}',
            'activo': idx_actual >= 1,
            'completado': idx_actual > 1
        },
        {
            'titulo': 'CONTROL DE CALIDAD Y CERTIFICACIÓN VIP',
            'sub': f'Aprobado 100% Auténtico • {f1}',
            'activo': idx_actual >= 2,
            'completado': idx_actual > 2
        },
        {
            'titulo': 'DESPACHO INTERNACIONAL DHL EXPRESS',
            'sub': f'Guía {orden.dhl_tracking} • {f2}',
            'activo': idx_actual >= 3,
            'completado': idx_actual > 3
        },
        {
            'titulo': 'DISPONIBLE PARA RETIRO EN FLAGSHIP O ENTREGA FINAL',
            'sub': f'Destino: {orden.ciudad} • {f3}',
            'activo': idx_actual >= 5,
            'completado': idx_actual >= 5
        }
    ]
    return pasos

@never_cache
@login_required(login_url='login')
def informacion(request):
    return render(request, 'locales/informacion.html')

@never_cache
@login_required(login_url='login')
def crear_preorden(request):
    if request.method == 'POST':
        idempotency_key = request.POST.get('idempotency_key', '').strip()
        if idempotency_key and len(idempotency_key) > 64:
            return redirect('/locales/informacion/?error=solicitud_invalida')
        if idempotency_key:
            existing_request = CheckoutRequest.objects.filter(
                usuario=request.user,
                key=idempotency_key,
            ).select_related('orden').first()
            if existing_request and existing_request.orden_id:
                existing_order = existing_request.orden
                return redirect(f'/locales/informacion/?codigo={existing_order.codigo_orden}&creada=1')

        nombre = request.user.get_full_name() or request.user.username
        email = request.user.email
        telefono = request.POST.get('telefono_cliente', '').strip()
        direccion = request.POST.get('direccion_entrega', '').strip()
        ciudad = request.POST.get('ciudad', 'Santiago').strip()
        producto_id = request.POST.get('producto_id')
        talla = request.POST.get('talla', 'M').strip()
        notas = request.POST.get('notas', '').strip()

        if not nombre or not email or not producto_id or not direccion:
            return redirect('/locales/informacion/?error=campos_incompletos')

        producto = get_object_or_404(Producto, id=producto_id)

        random_num = random.randint(1000, 9999)
        codigo_orden = f"SL-2026-{random_num}"
        while PreOrden.objects.filter(codigo_orden=codigo_orden).exists():
            random_num = random.randint(1000, 9999)
            codigo_orden = f"SL-2026-{random_num}"

        dhl_code = f"DHL-CL-{random.randint(10000000, 99999999)}"
        fecha_est = date.today() + timedelta(days=10)

        try:
            with transaction.atomic():
                checkout_request = None
                if idempotency_key:
                    checkout_request = CheckoutRequest.objects.create(
                        usuario=request.user,
                        key=idempotency_key,
                    )
                orden = PreOrden.objects.create(
                    codigo_orden=codigo_orden,
                    usuario=request.user,
                    nombre_cliente=nombre,
                    email_cliente=email,
                    telefono_cliente=telefono,
                    direccion_entrega=direccion,
                    ciudad=ciudad,
                    producto=producto,
                    talla=talla,
                    cantidad=1,
                    precio_total=producto.precio,
                    notas=notas,
                    estado='CONFIRMADA',
                    dhl_tracking=dhl_code,
                    fecha_estimada_entrega=fecha_est
                )
                if checkout_request:
                    checkout_request.orden = orden
                    checkout_request.save(update_fields=['orden'])
        except IntegrityError:
            if idempotency_key:
                existing_request = CheckoutRequest.objects.filter(
                    usuario=request.user,
                    key=idempotency_key,
                ).select_related('orden').first()
                if existing_request and existing_request.orden_id:
                    existing_order = existing_request.orden
                    return redirect(f'/locales/informacion/?codigo={existing_order.codigo_orden}&creada=1')
            raise

        enviar_correo_preorden(orden)

        return redirect(f'/locales/informacion/?codigo={orden.codigo_orden}&creada=1')

    return redirect('/locales/informacion/')

@never_cache
def api_rastrear(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Inicia sesión para consultar tus pedidos.'}, status=401)
    codigo = ''
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            codigo = data.get('codigo', '').strip()
        except Exception:
            codigo = request.POST.get('codigo', '').strip()
    else:
        codigo = request.GET.get('codigo', '').strip()

    if not codigo:
        return JsonResponse({'success': False, 'error': 'Debes ingresar un número de orden o código de reserva.'}, status=400)

    orden = PreOrden.objects.filter(
        codigo_orden__iexact=codigo,
        usuario=request.user,
    ).select_related('producto').first()
    if not orden:
        return JsonResponse({
            'success': False,
            'error': f"No se encontró ninguna pre-orden registrada con el código '{codigo}'. Verifica el número o realiza una nueva reserva."
        }, status=404)

    timeline = get_timeline_para_orden(orden)

    return JsonResponse({
        'success': True,
        'codigo': orden.codigo_orden,
        'cliente': orden.nombre_cliente,
        'email': orden.email_cliente,
        'telefono': orden.telefono_cliente,
        'direccion': orden.direccion_entrega,
        'ciudad': orden.ciudad,
        'producto': {
            'id': orden.producto.id,
            'nombre': orden.producto.nombre,
            'imagen': orden.producto.imagen,
            'precio_fmt': orden.precio_formateado(),
            'precio_usd': str(orden.producto.precio_usd),
        },
        'talla': orden.talla,
        'estado_raw': orden.estado,
        'estado_label': orden.get_estado_display(),
        'porcentaje_progreso': orden.porcentaje_progreso(),
        'dhl_tracking': orden.dhl_tracking,
        'fecha_creacion': orden.fecha_creacion.strftime('%d/%m/%Y'),
        'fecha_estimada': orden.fecha_estimada_entrega.strftime('%d/%m/%Y') if orden.fecha_estimada_entrega else 'En proceso',
        'timeline': timeline,
    })

@never_cache
def api_crear_preorden(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Inicia sesión para realizar una compra.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    idempotency_key = str(
        data.get('idempotency_key') or request.headers.get('Idempotency-Key') or ''
    ).strip()
    if len(idempotency_key) > 64:
        return JsonResponse({'success': False, 'error': 'La solicitud de compra no es válida.'}, status=400)
    if idempotency_key:
        existing_request = CheckoutRequest.objects.filter(
            usuario=request.user,
            key=idempotency_key,
        ).select_related('orden__producto').first()
        if existing_request and existing_request.orden_id:
            return _existing_order_response(existing_request.orden)

    nombre = request.user.get_full_name() or request.user.username
    email = request.user.email
    telefono = (data.get('telefono_cliente') or data.get('telefono') or '').strip()
    direccion = (data.get('direccion_entrega') or data.get('direccion') or '').strip()
    ciudad = (data.get('ciudad') or 'La Serena').strip()
    producto_id = data.get('producto_id') or data.get('id')
    talla = (data.get('talla') or 'M').strip()
    notas = (data.get('notas') or '').strip()

    has_items_key = 'items' in data
    items_list = data.get('items', [])
    processed_items = []
    calc_total = 0
    desc_items = []

    if has_items_key or items_list:
        if not isinstance(items_list, list) or len(items_list) == 0:
            return JsonResponse({'success': False, 'error': 'El carrito de compras está vacío o no contiene artículos válidos.'}, status=400)
        
        for it in items_list:
            it_id = it.get('id')
            if not it_id:
                return JsonResponse({'success': False, 'error': 'ID de producto faltante en el carrito.'}, status=400)
            try:
                p_item = Producto.objects.get(id=it_id)
            except (Producto.DoesNotExist, ValueError):
                return JsonResponse({'success': False, 'error': f'El producto con ID {it_id} no existe en el catálogo.'}, status=400)
            
            raw_qty = it.get('quantity', 1)
            try:
                qty = int(raw_qty)
                if qty <= 0 or qty > 50:
                    return JsonResponse({'success': False, 'error': f'Cantidad inválida ({raw_qty}) para "{p_item.nombre}". Debe ser entre 1 y 50.'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': f'Cantidad no numérica para "{p_item.nombre}".'}, status=400)
            
            it_size = (it.get('size') or it.get('talla') or talla or 'M').strip()
            subtotal_item = p_item.precio * qty
            calc_total += subtotal_item
            desc_items.append(f"• {p_item.nombre} (Talla: {it_size}, Cant: {qty}) — ${subtotal_item:,} CLP".replace(',', '.'))
            processed_items.append({'producto': p_item, 'cantidad': qty, 'talla': it_size, 'subtotal': subtotal_item})

        producto = processed_items[0]['producto']
        talla = processed_items[0]['talla']
        precio_total = calc_total
        notas = f"Pedido de Bolsa ({len(processed_items)} ítems):\n" + "\n".join(desc_items) + (f"\n\nNotas adicionales: {notas}" if notas else "")
    else:
        if not producto_id:
            return JsonResponse({'success': False, 'error': 'Debes especificar un producto para realizar la compra.'}, status=400)
        try:
            producto = Producto.objects.get(id=producto_id)
        except (Producto.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': f'El producto con ID {producto_id} no existe en el catálogo.'}, status=400)
        
        raw_qty = data.get('cantidad', 1)
        try:
            cantidad = int(raw_qty)
            if cantidad <= 0 or cantidad > 50:
                return JsonResponse({'success': False, 'error': f'Cantidad inválida ({raw_qty}). Debe ser entre 1 y 50.'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Cantidad no numérica.'}, status=400)
        
        precio_total = producto.precio * cantidad

    random_num = random.randint(1000, 9999)
    codigo_orden = f"SL-2026-{random_num}"
    while PreOrden.objects.filter(codigo_orden=codigo_orden).exists():
        random_num = random.randint(1000, 9999)
        codigo_orden = f"SL-2026-{random_num}"

    dhl_code = f"DHL-CL-{random.randint(10000000, 99999999)}"
    fecha_est = date.today() + timedelta(days=10)
    user = request.user

    cupon_codigo = (data.get('cupon') or data.get('cupon_codigo') or '').strip().upper()
    descuento_aplicado = 0
    cliente_cupon_a_consumir = None

    if cupon_codigo:
        from usuarios.models import Cliente
        cliente_dueno = Cliente.objects.filter(cupon_bienvenida_codigo__iexact=cupon_codigo).first()

        if cupon_codigo == 'SOLARY15':
            if not user or not hasattr(user, 'cliente'):
                return JsonResponse({
                    'success': False,
                    'error': 'Debes iniciar sesión con tu cuenta para utilizar el cupón de bienvenida SOLARY15.'
                }, status=400)
            if user.cliente.cupon_usado:
                return JsonResponse({
                    'success': False,
                    'error': 'El cupón de bienvenida ya ha sido utilizado por esta cuenta.'
                }, status=400)
            cliente_cupon_a_consumir = user.cliente
        elif cliente_dueno:
            if cliente_dueno.cupon_usado:
                return JsonResponse({
                    'success': False,
                    'error': 'Este cupón de bienvenida ya fue utilizado anteriormente.'
                }, status=400)
            if user and cliente_dueno.user != user:
                return JsonResponse({
                    'success': False,
                    'error': 'El cupón ingresado no corresponde a tu cuenta de usuario.'
                }, status=400)
            elif not user and email and cliente_dueno.user.email.lower() != email.lower():
                return JsonResponse({
                    'success': False,
                    'error': 'El cupón ingresado no corresponde al correo del comprador.'
                }, status=400)
            cliente_cupon_a_consumir = cliente_dueno
        else:
            return JsonResponse({
                'success': False,
                'error': f"El cupón '{cupon_codigo}' no es válido o ha expirado."
            }, status=400)

        descuento_aplicado = int(precio_total * 0.15)
        precio_total = max(0, precio_total - descuento_aplicado)
        notas = f"[CUPÓN APLICADO: {cupon_codigo} (-15% = -${descuento_aplicado:,} CLP)]\n".replace(',', '.') + notas

    items_a_reservar = processed_items if processed_items else [{'producto': producto, 'cantidad': cantidad, 'talla': talla}]

    try:
        with transaction.atomic():
            checkout_request = None
            if idempotency_key:
                checkout_request = CheckoutRequest.objects.create(
                    usuario=request.user,
                    key=idempotency_key,
                )
            for it_res in items_a_reservar:
                p_obj = it_res['producto']
                c_qty = it_res['cantidad']
                t_nom = it_res.get('talla', 'M')

                pt_qs = ProductoTalla.objects.select_for_update().filter(producto=p_obj)
                pt = pt_qs.filter(talla__nombre__iexact=t_nom).first()
                if not pt:
                    pt = pt_qs.first()

                if pt:
                    updated = ProductoTalla.objects.filter(
                        pk=pt.pk,
                        stock__gte=c_qty,
                    ).update(stock=F('stock') - c_qty)
                    if not updated:
                        stock_available = ProductoTalla.objects.filter(pk=pt.pk).values_list('stock', flat=True).first() or 0
                        raise InsufficientStockError(
                            f'Stock insuficiente para "{p_obj.nombre}" (Talla: {t_nom}). '
                            f'Stock disponible: {stock_available}.'
                        )

            if cliente_cupon_a_consumir:
                from django.utils import timezone
                cliente_cupon_a_consumir.cupon_usado = True
                cliente_cupon_a_consumir.fecha_canje_cupon = timezone.now()
                cliente_cupon_a_consumir.save(update_fields=['cupon_usado', 'fecha_canje_cupon'])

            orden = PreOrden.objects.create(
                codigo_orden=codigo_orden,
                usuario=user,
                nombre_cliente=nombre,
                email_cliente=email,
                telefono_cliente=telefono,
                direccion_entrega=direccion or 'Av. del Mar / Cuatro Esquinas (Atelier La Serena)',
                ciudad=ciudad or 'La Serena',
                producto=producto,
                talla=talla or 'M',
                cantidad=sum(x['cantidad'] for x in items_a_reservar),
                precio_total=precio_total,
                notas=notas,
                estado='CONFIRMADA',
                dhl_tracking=dhl_code,
                fecha_estimada_entrega=fecha_est
            )
            if checkout_request:
                checkout_request.orden = orden
                checkout_request.save(update_fields=['orden'])
    except InsufficientStockError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        if idempotency_key:
            existing_request = CheckoutRequest.objects.filter(
                usuario=request.user,
                key=idempotency_key,
            ).select_related('orden__producto').first()
            if existing_request and existing_request.orden_id:
                return _existing_order_response(existing_request.orden)
        logger.error('Purchase processing failed (exception=%s)', type(exc).__name__)
        return JsonResponse({
            'success': False,
            'error': 'No pudimos procesar tu pedido. Intenta nuevamente o contacta a soporte.'
        }, status=500)

    correo_enviado = enviar_correo_preorden(orden)
    if correo_enviado:
        mensaje = f"¡Pedido #{orden.codigo_orden} confirmado. El comprobante fue enviado a {email}."
    else:
        mensaje = (
            f"¡Pedido #{orden.codigo_orden} confirmado, pero no pudimos enviar el comprobante. "
            'Contacta a soporte si necesitas una copia.'
        )

    return JsonResponse({
        'success': True,
        'codigo_orden': orden.codigo_orden,
        'mensaje': mensaje,
        'correo_enviado': correo_enviado,
        'email': email,
        'dhl_tracking': orden.dhl_tracking,
        'precio_fmt': orden.precio_formateado(),
        'descuento_aplicado': descuento_aplicado,
        'tracking_url': f"/locales/informacion/?codigo={orden.codigo_orden}"
    })

@never_cache
def api_validar_cupon(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Inicia sesión para validar tu cupón.'}, status=401)
    codigo = (request.GET.get('codigo') or request.POST.get('codigo') or '').strip().upper()
    if not codigo:
        return JsonResponse({'success': False, 'error': 'Ingresa un código de descuento.'}, status=400)

    from usuarios.models import Cliente
    es_valido = (codigo == 'SOLARY15') or Cliente.objects.filter(cupon_bienvenida_codigo__iexact=codigo).exists()

    if es_valido:
        return JsonResponse({
            'success': True,
            'codigo': codigo,
            'descuento_porcentaje': 15,
            'mensaje': '✓ Cupón VIP aplicado: 15% de descuento en tu compra.'
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'El código de cupón ingresado no es válido o ha expirado.'
        }, status=404)

def api_dolar(request):
    valor_raw = 965.71
    try:
        response = requests.get('https://mindicador.cl/api/dolar', timeout=2.5)
        if response.status_code == 200:
            data = response.json()
            series = data.get('serie', [])
            if series:
                valor_raw = float(series[0].get('valor', 965.71))
    except Exception:
        pass

    return JsonResponse({
        'success': True,
        'dolar': valor_raw,
        'dolar_fmt': f"${valor_raw:,.2f} CLP",
    })

