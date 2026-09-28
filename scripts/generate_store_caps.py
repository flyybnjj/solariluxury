import asyncio
import os
import sys
import shutil
import time
import subprocess
import urllib.request
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESKTOP_DIR = r"C:\Users\avalo\Desktop\caps"
PROJECT_CAPS_DIR = os.path.join(BASE_DIR, "capturas_sitio")
os.makedirs(DESKTOP_DIR, exist_ok=True)
os.makedirs(PROJECT_CAPS_DIR, exist_ok=True)

PORT = 8080
SERVER_URL = f"http://127.0.0.1:{PORT}"

def wait_for_server(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

async def capture_all():
    print(f"Iniciando captura completa de la tienda actualizada en: {DESKTOP_DIR} ...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context_desktop = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            device_scale_factor=1.5
        )
        page = await context_desktop.new_page()

        async def save_shot(filename, full_page=False):
            dest_desktop = os.path.join(DESKTOP_DIR, filename)
            dest_proj = os.path.join(PROJECT_CAPS_DIR, filename)
            data = await page.screenshot(full_page=full_page)
            for path in [dest_desktop, dest_proj]:
                try:
                    with open(path, "wb") as f:
                        f.write(data)
                except Exception as e:
                    print(f"Nota: archivo en uso temporal ({filename}): {e}")
            print(f"[OK] Capturado: {filename}")

        # 1. HOME / PORTADA
        print("1. Portada...")
        await page.goto(f"{SERVER_URL}/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1000)
        await save_shot("01_home_hero_desktop.png")

        # 2. CATÁLOGO COMPLETO CON NUEVOS PRODUCTOS SCRAPEADOS
        print("2. Catálogo General...")
        await page.goto(f"{SERVER_URL}/productos/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1200)
        await page.evaluate("window.scrollTo(0, 160)")
        await page.wait_for_timeout(600)
        await save_shot("02_catalogo_vault_alineacion.png")

        # 3. HOVER / EFECTO CROSSFADE & 360 SCRUBBER EN TARJETA
        print("3. Catálogo Hover...")
        await page.evaluate("""() => {
            const card = document.querySelector(".prod-card[data-is-360='true']") || document.querySelector(".prod-card");
            if (card) {
                const hoverImg = card.querySelector('.pc-img-hover');
                if (hoverImg) {
                    hoverImg.style.opacity = '1';
                }
                const sizeBar = card.querySelector('.pc-size-bar');
                if (sizeBar) {
                    sizeBar.style.transform = 'translateY(0)';
                    sizeBar.style.opacity = '1';
                }
            }
        }""")
        await page.wait_for_timeout(600)
        await save_shot("03_catalogo_tarjeta_hover.png")

        # 4. FILTRADO POR CALZADO / SNEAKERS CON BADGES 360°
        print("4. Filtrando Zapatillas...")
        await page.evaluate("""() => {
            const chip = Array.from(document.querySelectorAll('.cat-badge-chip')).find(c => c.textContent.includes('Calzado') || c.textContent.includes('Sneakers'));
            if (chip && typeof filterCatalogCategory === 'function') {
                filterCatalogCategory(chip.dataset.cat, chip);
            }
        }""")
        await page.wait_for_timeout(1000)
        await save_shot("04_catalogo_calzado_sneakers_360.png")

        # 5. MODAL QUICK VIEW
        print("5. Quick View...")
        await page.evaluate("""() => {
            const btn = document.querySelector(".prod-card[data-is-360='true'] .pc-quickview-btn") || document.querySelector(".pc-quickview-btn");
            if (btn && typeof openQuickView === 'function') {
                openQuickView(new MouseEvent('click'), btn);
            }
        }""")
        await page.wait_for_timeout(1000)
        await save_shot("05_catalogo_modal_quickview.png")

        await page.evaluate("() => { if (typeof closeQuickView === 'function') closeQuickView(); }")
        await page.wait_for_timeout(400)

        # 6. PRODUCTO DETALLE: JORDAN 4 RETRO TORO BRAVO (ID 46) CON SLIDER STOCKX 360°
        print("6. Detalle Jordan 4 Toro Bravo (StockX 360 Slider)...")
        await page.goto(f"{SERVER_URL}/productos/46/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1200)
        await save_shot("06_detalle_jordan4_toro_bravo_stockx_360.png")

        # 7. GIRAR LA ZAPATILLA CON EL SLIDER STOCKX
        print("7. Rotación de Zapatilla Ángulo Posterior...")
        await page.evaluate("""() => {
            if (typeof updateAngleView === 'function') {
                updateAngleView(5); // Ángulo de perfil posterior
            }
        }""")
        await page.wait_for_timeout(800)
        await save_shot("07_detalle_jordan4_rotada_angulo5.png")

        # 8. DETALLE OTRA PRENDA: SUDADERA / ABRIGO TRAPSTAR
        print("8. Detalle Prenda...")
        await page.goto(f"{SERVER_URL}/productos/34/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1000)
        await save_shot("08_detalle_prenda_abrigo_trapstar.png")

        # 9. PÁGINA DE LOCALES VACÍA Y LIMPIA
        print("9. Locales Vacía...")
        await page.goto(f"{SERVER_URL}/locales/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1000)
        await save_shot("09_locales_pagina_limpia_vacia.png")

        # 10. LOGIN Y SISTEMA DE USUARIOS
        print("10. Pantalla de Login...")
        await page.goto(f"{SERVER_URL}/login/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1000)
        await save_shot("10_login_sistema_usuarios.png")

        # 11. REGISTRO DE NUEVO USUARIO
        print("11. Pantalla de Registro...")
        await page.goto(f"{SERVER_URL}/registro/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1000)
        await save_shot("11_registro_nuevo_usuario.png")

        # 12. INICIAR SESIÓN COMO ADMINISTRADOR Y VER EL PANEL PRIVILEGIADO
        print("12. Login de Administrador...")
        await page.fill("input[name='username']", "admin")
        await page.fill("input[name='password']", "Solariluxury2026!")
        await page.click("button[type='submit']")
        await page.wait_for_timeout(1500)
        
        # Desplegar panel admin
        await page.goto(f"{SERVER_URL}/productos/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(800)
        await page.evaluate("""() => {
            const btn = document.getElementById('subHeaderPanelBtn');
            if (btn && typeof toggleAppleTray === 'function') {
                toggleAppleTray('subHeaderPanelTray', btn);
            }
        }""")
        await page.wait_for_timeout(700)
        await save_shot("12_panel_admin_exclusivo_staff.png")

        await context_desktop.close()

        # 13. VISTAS MOBILE
        print("13. Vista Móvil...")
        context_mobile = await browser.new_context(
            viewport={'width': 390, 'height': 844},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=2
        )
        page_mobile = await context_mobile.new_page()

        async def save_shot_mobile(filename):
            dest_desktop = os.path.join(DESKTOP_DIR, filename)
            dest_proj = os.path.join(PROJECT_CAPS_DIR, filename)
            data = await page_mobile.screenshot()
            for path in [dest_desktop, dest_proj]:
                try:
                    with open(path, "wb") as f:
                        f.write(data)
                except Exception as e:
                    print(f"Nota: archivo móvil en uso temporal ({filename}): {e}")
            print(f"[OK] Capturado Móvil: {filename}")

        await page_mobile.goto(f"{SERVER_URL}/productos/", wait_until="domcontentloaded", timeout=20000)
        await page_mobile.wait_for_timeout(1000)
        await page_mobile.evaluate("window.scrollTo(0, 160)")
        await page_mobile.wait_for_timeout(600)
        await save_shot_mobile("13_movil_catalogo_grilla.png")

        await page_mobile.goto(f"{SERVER_URL}/productos/46/", wait_until="domcontentloaded", timeout=20000)
        await page_mobile.wait_for_timeout(1000)
        await save_shot_mobile("14_movil_detalle_stockx_360.png")

        await context_mobile.close()
        await browser.close()
        print("\n[ÉXITO] ¡Todas las nuevas capturas se guardaron correctamente en C:\\Users\\avalo\\Desktop\\caps!")

def main():
    manage_py = os.path.join(BASE_DIR, "mi_proyecto", "manage.py")
    server_process = subprocess.Popen(
        [sys.executable, manage_py, "runserver", f"127.0.0.1:{PORT}", "--noreload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    try:
        print(f"Esperando que el servidor Django inicie en {SERVER_URL}...")
        if not wait_for_server(SERVER_URL, timeout=15):
            print("Error: No se pudo conectar al servidor Django.")
            return 1
        print("Servidor Django activo.")
        asyncio.run(capture_all())
    finally:
        server_process.terminate()
        server_process.wait()
        print("Servidor Django cerrado.")

if __name__ == '__main__':
    sys.exit(main() or 0)
