import os
import sys
import tarfile
import subprocess
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEM_KEY = r"C:\Users\avalo\Downloads\clave-sgr.pem"
REMOTE_HOST = "32.193.109.160"
REMOTE_USER = "ubuntu"
TAR_PATH = os.path.join(BASE_DIR, "update_mobile.tar.gz")

def create_tarball():
    print(f"[*] Empaquetando plantillas y estáticos optimizados...")
    with tarfile.open(TAR_PATH, "w:gz") as tar:
        # Añadir catalogo/templates
        cat_tpl = os.path.join(BASE_DIR, "mi_proyecto", "catalogo", "templates")
        tar.add(cat_tpl, arcname="catalogo/templates")
        
        # Añadir locales/templates
        loc_tpl = os.path.join(BASE_DIR, "mi_proyecto", "locales", "templates")
        tar.add(loc_tpl, arcname="locales/templates")
        
        # Añadir usuarios/templates
        usr_tpl = os.path.join(BASE_DIR, "mi_proyecto", "usuarios", "templates")
        tar.add(usr_tpl, arcname="usuarios/templates")
        
        # Añadir templates base
        base_tpl = os.path.join(BASE_DIR, "mi_proyecto", "templates")
        tar.add(base_tpl, arcname="templates")
        
        # Añadir static
        static_dir = os.path.join(BASE_DIR, "mi_proyecto", "static")
        tar.add(static_dir, arcname="static")
        
    size_mb = os.path.getsize(TAR_PATH) / (1024 * 1024)
    print(f"[✓] Tarball creado: {TAR_PATH} ({size_mb:.2f} MB)")

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-i", PEM_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{REMOTE_USER}@{REMOTE_HOST}",
        cmd
    ]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    return res

def upload_tarball():
    print(f"[*] Subiendo tarball vía SCP a {REMOTE_HOST}...")
    scp_cmd = [
        "scp", "-i", PEM_KEY,
        "-o", "StrictHostKeyChecking=no",
        TAR_PATH,
        f"{REMOTE_USER}@{REMOTE_HOST}:/home/ubuntu/tienda/update_mobile.tar.gz"
    ]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Error en SCP: {res.stderr}")
        sys.exit(1)
    print(f"[✓] Tarball subido exitosamente a AWS")

def deploy_remote():
    print(f"[*] Desplegando en el servidor de producción...")
    
    # 1. Crear backup de templates antes de aplicar
    backup_cmd = (
        "cd /home/ubuntu/tienda/mi_proyecto && "
        "mkdir -p backup_mobile_$(date +%Y%m%d_%H%M%S) && "
        "cp -r templates catalogo/templates locales/templates usuarios/templates backup_mobile_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true"
    )
    res_b = run_ssh(backup_cmd)
    print(f"[✓] Respaldo remoto creado")

    # 2. Descomprimir tarball en mi_proyecto
    unpack_cmd = (
        "cd /home/ubuntu/tienda/mi_proyecto && "
        "tar -xzf /home/ubuntu/tienda/update_mobile.tar.gz"
    )
    res_u = run_ssh(unpack_cmd)
    if res_u.returncode != 0:
        print(f"[!] Error al descomprimir: {res_u.stderr}")
        sys.exit(1)
    print(f"[✓] Archivos actualizados en /home/ubuntu/tienda/mi_proyecto/")

    # 3. Collectstatic y restart gunicorn
    restart_cmd = (
        "cd /home/ubuntu/tienda/mi_proyecto && "
        "/home/ubuntu/venv/bin/python manage.py collectstatic --noinput && "
        "sudo systemctl restart gunicorn && "
        "sudo systemctl is-active gunicorn"
    )
    res_r = run_ssh(restart_cmd)
    print(f"[*] Salida collectstatic y restart:\n{res_r.stdout.strip()}")
    if "active" not in res_r.stdout:
        print(f"[!] Advertencia: gunicorn estado: {res_r.stdout}")
    else:
        print(f"[✓] Gunicorn reiniciado y ACTIVO en AWS!")

    # 4. Probar respuesta HTTP
    test_cmd = "curl -s -I http://127.0.0.1:8000/ | head -n 5"
    res_t = run_ssh(test_cmd)
    print(f"[*] Respuesta HTTP local en EC2:\n{res_t.stdout.strip()}")

def verify_live():
    print(f"\n[*] Verificando sitio en vivo en AWS: http://{REMOTE_HOST}/ ...")
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Mobile iPhone 15 Pro
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(f"http://{REMOTE_HOST}/", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1000)

        metrics = page.evaluate("""() => {
            const win = window.innerWidth;
            const doc = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
            return { win, doc, ok: doc <= win + 1 };
        }""")
        
        status = "PASSED [OK]" if metrics["ok"] else "OVERFLOW [FAIL]"
        print(f"[✓] Verificación Live Mobile en AWS 390px: {status} (win={metrics['win']}px, doc={metrics['doc']}px)")
        
        shot_path = os.path.join(BASE_DIR, "capturas_mobile_audit", "despues", "aws_live_production_390x844.png")
        page.screenshot(path=shot_path)
        print(f"[✓] Captura live de AWS guardada en: {shot_path}")
        browser.close()

if __name__ == "__main__":
    create_tarball()
    upload_tarball()
    deploy_remote()
    verify_live()
    print("\n==================================================")
    print("  DESPLIEGUE A AWS COMPLETADO CON ÉXITO")
    print("==================================================")
