import json
import random
import requests
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import F
from .models import Local
from catalogo.models import Producto, PreOrden, ProductoTalla


def lista_locales(request):
    locales = Local.objects.filter(activo=True)
    context = {
        'locales': locales,
        'total_locales': locales.count(),
    }
    return render(request, 'locales/lista_locales.html', context)


from django.template.loader import render_to_string


def enviar_correo_preorden(orden):
    """Envía un correo de notificación de pedido con diseño Apple minimalista conforme al estado actual"""
    fecha_entrega_str = orden.fecha_estimada_entrega.strftime('%d de %B de %Y') if orden.fecha_estimada_entrega else 'Por coordinar'
    tracking_url = f"http://127.0.0.1:8000/locales/informacion/?codigo={orden.codigo_orden}"

    # Calcular desglose
    total_val = orden.precio_total or (orden.producto.precio * orden.cantidad)
    neto_val = round(total_val / 1.19)
    iva_val = total_val - neto_val

    subtotal_str = f"${total_val:,.0f} CLP".replace(',', '.')
    iva_str = f"${iva_val:,.0f} CLP".replace(',', '.')

    img_rel = orden.producto.imagen.lstrip('/') if orden.producto.imagen else 'img/placeholder.jpg'
    img_abs = f"http://127.0.0.1:8000/static/{img_rel}"
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
    except Exception as e:
        print(f"[EMAIL ERROR]: {e}")
        return False


def get_timeline_para_orden(orden):
    """Genera las 4 etapas del tracking para una orden dada"""
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


def informacion(request):
    """Página de Preventa, Tipo de Cambio en Vivo y Seguimiento Logístico"""
    valor_dolar = "No disponible"
    estado_api = "Sin conexion"
    try:
        response = requests.get('https://mindicador.cl/api/dolar', timeout=2.5)
        if response.status_code == 200:
            datos = response.json()
            valor_raw = datos['serie'][0]['valor']
            valor_dolar = f"{valor_raw:.2f}".replace('.', ',')
            estado_api = "Conexion en tiempo real exitosa"
        else:
            valor_dolar = "940,50 (Estimado)"
            estado_api = "Modo contingencia / API en espera"
    except Exception:
        valor_dolar = "940,50 (Estimado)"
        estado_api = "Modo contingencia / Fuera de linea"

    # Buscar orden si viene por GET param o POST
    codigo_query = request.GET.get('codigo', '').strip()
    orden_encontrada = None
    timeline = []
    error_busqueda = None

    if codigo_query:
        orden_encontrada = PreOrden.objects.filter(codigo_orden__iexact=codigo_query).select_related('producto').first()
        if orden_encontrada:
            timeline = get_timeline_para_orden(orden_encontrada)
        else:
            error_busqueda = f"No se encontró ninguna pre-orden registrada con el código '{codigo_query}'."

    productos_preventa = Producto.objects.all().order_by('id')

    context = {
        'dolar': valor_dolar,
        'estado_api': estado_api,
        'productos': productos_preventa,
        'codigo_query': codigo_query,
        'orden': orden_encontrada,
        'timeline': timeline,
        'error_busqueda': error_busqueda,
        'total_productos': productos_preventa.count(),
    }
    return render(request, 'locales/informacion.html', context)


def crear_preorden(request):
    """Procesa la reserva de una pre-orden y envía correo de confirmación"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre_cliente', '').strip()
        email = request.POST.get('email_cliente', '').strip()
        telefono = request.POST.get('telefono_cliente', '').strip()
        direccion = request.POST.get('direccion_entrega', '').strip()
        ciudad = request.POST.get('ciudad', 'Santiago').strip()
        producto_id = request.POST.get('producto_id')
        talla = request.POST.get('talla', 'M').strip()
        notas = request.POST.get('notas', '').strip()

        if not nombre or not email or not producto_id or not direccion:
            return redirect('/locales/informacion/?error=campos_incompletos')

        producto = get_object_or_404(Producto, id=producto_id)

        # Generar código único SL-2026-XXXX
        random_num = random.randint(1000, 9999)
        codigo_orden = f"SL-2026-{random_num}"
        while PreOrden.objects.filter(codigo_orden=codigo_orden).exists():
            random_num = random.randint(1000, 9999)
            codigo_orden = f"SL-2026-{random_num}"

        dhl_code = f"DHL-CL-{random.randint(10000000, 99999999)}"
        fecha_est = date.today() + timedelta(days=10)

        orden = PreOrden.objects.create(
            codigo_orden=codigo_orden,
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

        # Enviar correo de confirmación
        enviar_correo_preorden(orden)

        return redirect(f'/locales/informacion/?codigo={orden.codigo_orden}&creada=1')

    return redirect('/locales/informacion/')


@csrf_exempt
def api_rastrear(request):
    """API JSON para rastreo de orden por código"""
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

    orden = PreOrden.objects.filter(codigo_orden__iexact=codigo).select_related('producto').first()
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


@csrf_exempt
def api_crear_preorden(request):
    """API JSON para crear una pre-orden desde modales o carritos y enviar correo"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    nombre = (data.get('nombre_cliente') or data.get('nombre') or '').strip()
    email = (data.get('email_cliente') or data.get('email') or '').strip()
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

    if not nombre and request.user.is_authenticated:
        nombre = request.user.get_full_name() or request.user.username
    if not email and request.user.is_authenticated:
        email = request.user.email

    if not nombre:
        nombre = 'Cliente Solary VIP'
    if not email:
        email = 'cliente@solaryluxury.com'

    random_num = random.randint(1000, 9999)
    codigo_orden = f"SL-2026-{random_num}"
    while PreOrden.objects.filter(codigo_orden=codigo_orden).exists():
        random_num = random.randint(1000, 9999)
        codigo_orden = f"SL-2026-{random_num}"

    dhl_code = f"DHL-CL-{random.randint(10000000, 99999999)}"
    fecha_est = date.today() + timedelta(days=10)
    user = request.user if request.user.is_authenticated else None
    if not user and email:
        from django.contrib.auth.models import User
        user = User.objects.filter(email__iexact=email).first()

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
            # 1. Validar y descontar stock con select_for_update()
            for it_res in items_a_reservar:
                p_obj = it_res['producto']
                c_qty = it_res['cantidad']
                t_nom = it_res.get('talla', 'M')

                pt_qs = ProductoTalla.objects.select_for_update().filter(producto=p_obj)
                pt = pt_qs.filter(talla__nombre__iexact=t_nom).first()
                if not pt:
                    pt = pt_qs.first()

                if pt:
                    if pt.stock < c_qty:
                        return JsonResponse({
                            'success': False,
                            'error': f'Stock insuficiente para "{p_obj.nombre}" (Talla: {t_nom}). Stock disponible: {pt.stock}.'
                        }, status=400)
                    pt.stock = F('stock') - c_qty
                    pt.save(update_fields=['stock'])

            # 2. Si se utilizó cupón, marcarlo como consumido
            if cliente_cupon_a_consumir:
                from django.utils import timezone
                cliente_cupon_a_consumir.cupon_usado = True
                cliente_cupon_a_consumir.fecha_canje_cupon = timezone.now()
                cliente_cupon_a_consumir.save(update_fields=['cupon_usado', 'fecha_canje_cupon'])

            # 3. Crear la Pre-Orden oficial dentro de la transacción
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
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al procesar la compra: {str(e)}'}, status=500)

    # Enviar correo de confirmación
    correo_enviado = enviar_correo_preorden(orden)

    return JsonResponse({
        'success': True,
        'codigo_orden': orden.codigo_orden,
        'mensaje': f"¡Compra #{orden.codigo_orden} confirmada exitosamente! Se ha enviado el comprobante a {email}.",
        'correo_enviado': correo_enviado,
        'email': email,
        'dhl_tracking': orden.dhl_tracking,
        'precio_fmt': orden.precio_formateado(),
        'descuento_aplicado': descuento_aplicado,
        'tracking_url': f"/locales/informacion/?codigo={orden.codigo_orden}"
    })


def api_validar_cupon(request):
    """Valida si un código de cupón es válido (personal de usuario o código general)"""
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
    """Retorna el tipo de cambio oficial en vivo USD/CLP de mindicador.cl para conversiones automáticas"""
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

