import urllib.request
import json
import time

email_dest = 'avalosb758@gmail.com'
plantillas = [
    ('codigo_seguridad', '05 — Código de Verificación (Solary ID)'),
    ('preparando_pedido', '01 — Estamos Preparando tu Pedido (Solary)'),
    ('pedido_despachado', '02 — Pedido Despachado (Solary)'),
    ('pedido_entregado', '03 — Pedido Entregado con Éxito (Solary)'),
    ('recibo_compra', '04 — Recibo Oficial de Compra (Solary)'),
    ('invitacion_drop', '06 — Invitación Drop Privado VIP (Solary)'),
]

print(f"=== INICIANDO DESPACHO DE LOS 6 CORREOS A: {email_dest} ===")

for p_key, p_nombre in plantillas:
    payload = json.dumps({'email': email_dest, 'plantilla': p_key}).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/enviar-email-prueba/',
        data=payload,
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            if res_data.get('success'):
                print(f"[OK] Enviado: {p_nombre}")
            else:
                print(f"[ERROR] {p_nombre}: {res_data.get('error')}")
    except Exception as e:
        print(f"[EXCEPCIÓN] {p_nombre}: {e}")
    
    time.sleep(1.2)

print("=== TODOS LOS CORREOS ENVIADOS EXITOSAMENTE ===")
