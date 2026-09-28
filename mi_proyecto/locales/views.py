import json
import random
import requests
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import Local
from catalogo.models import Producto, PreOrden


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
    total_val = orden.precio_total or (orden.producto.precio_clp * orden.cantidad)
    neto_val = int(total_val / 1.19)
    iva_val = total_val - neto_val

    subtotal_str = f"${total_val:,.0f} CLP".replace(',', '.')
    iva_str = f"${iva_val:,.0f} CLP".replace(',', '.')

    ctx = {
        'orden': orden,
        'pedido_id': orden.codigo_orden,
        'cliente_nombre': orden.nombre_cliente,
        'producto_nombre': orden.producto.nombre,
        'producto_subtitulo': f"Central Cee Special Edition · {getattr(orden.producto, 'color', 'Black Edition') or 'Black Edition'}",
        'talla': orden.talla,
        'cantidad': orden.cantidad,
        'estilo': f"SL-{getattr(orden.producto, 'codigo_estilo', 'FZ4210-001') or 'FZ4210-001'}",
        'direccion': orden.direccion_entrega,
        'comuna': f"{orden.ciudad}, Región Metropolitana" if orden.ciudad else "Santiago",
        'fecha_estimada': fecha_entrega_str,
        'llegada_programada': fecha_entrega_str,
        'guia_dhl': orden.dhl_tracking,
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

    nombre = data.get('nombre_cliente', '').strip()
    email = data.get('email_cliente', '').strip()
    telefono = data.get('telefono_cliente', '').strip()
    direccion = data.get('direccion_entrega', '').strip()
    ciudad = data.get('ciudad', 'Santiago').strip()
    producto_id = data.get('producto_id')
    talla = data.get('talla', 'M').strip()
    notas = data.get('notas', '').strip()

    if not nombre or not email or not producto_id:
        return JsonResponse({'success': False, 'error': 'Faltan campos obligatorios (nombre, correo o producto).'}, status=400)

    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'El producto seleccionado no existe.'}, status=404)

    random_num = random.randint(1000, 9999)
    codigo_orden = f"SL-2026-{random_num}"
    while PreOrden.objects.filter(codigo_orden=codigo_orden).exists():
        random_num = random.randint(1000, 9999)
        codigo_orden = f"SL-2026-{random_num}"

    dhl_code = f"DHL-CL-{random.randint(10000000, 99999999)}"
    user = request.user if request.user.is_authenticated else None
    if not user and email:
        from django.contrib.auth.models import User
        user = User.objects.filter(email__iexact=email).first()

    orden = PreOrden.objects.create(
        codigo_orden=codigo_orden,
        usuario=user,
        nombre_cliente=nombre,
        email_cliente=email,
        telefono_cliente=telefono,
        direccion_entrega=direccion or 'Alonso de Córdova 3890 (Retiro Flagship)',
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
    correo_enviado = enviar_correo_preorden(orden)

    return JsonResponse({
        'success': True,
        'codigo_orden': orden.codigo_orden,
        'mensaje': f"¡Pre-orden #{orden.codigo_orden} confirmada exitosamente! Se ha enviado el comprobante a {email}.",
        'correo_enviado': correo_enviado,
        'email': email,
        'dhl_tracking': orden.dhl_tracking,
        'precio_fmt': orden.precio_formateado(),
        'tracking_url': f"/locales/informacion/?codigo={orden.codigo_orden}"
    })


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

