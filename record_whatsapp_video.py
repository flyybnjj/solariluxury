import os
import time
import shutil
import subprocess
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

CAPS_DIR = r"C:\Users\avalo\Desktop\caps"
CAP_DIR = r"C:\Users\avalo\Desktop\cap"
TEMP_VIDEO_DIR = r"C:\Users\avalo\Documents\tienda\temp_rec"

os.makedirs(CAPS_DIR, exist_ok=True)
os.makedirs(CAP_DIR, exist_ok=True)
if os.path.exists(TEMP_VIDEO_DIR):
    shutil.rmtree(TEMP_VIDEO_DIR, ignore_errors=True)
os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)

def record():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"[1/4] FFmpeg: {ffmpeg_exe}")

    with sync_playwright() as p:
        print("[2/4] Grabando flujo VIP completo...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu-vsync",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--hide-scrollbars",
                "--autoplay-policy=no-user-gesture-required"
            ]
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            device_scale_factor=1,
            record_video_dir=TEMP_VIDEO_DIR,
            record_video_size={'width': 1280, 'height': 720}
        )

        page = context.new_page()

        # Inyectar función de scroll ultra suave
        page.add_init_script("""
            window.smoothScrollTo = function(targetY, durationMs) {
                return new Promise(resolve => {
                    const startY = window.scrollY;
                    const diff = targetY - startY;
                    const startTime = performance.now();
                    function step(now) {
                        const elapsed = now - startTime;
                        const t = Math.min(1, elapsed / durationMs);
                        const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
                        window.scrollTo(0, startY + diff * ease);
                        if (t < 1) {
                            requestAnimationFrame(step);
                        } else {
                            window.scrollTo(0, targetY);
                            resolve();
                        }
                    }
                    requestAnimationFrame(step);
                });
            };
            window.smoothScrollBy = function(deltaY, durationMs) {
                return window.smoothScrollTo(window.scrollY + deltaY, durationMs);
            };
        """)

        print("Navegando al portal privado...")
        page.goto("http://127.0.0.1:8000/bloquear-tienda/", wait_until="domcontentloaded")
        page.evaluate("localStorage.removeItem('solariluxury_vip_unlocked');")
        page.reload()
        time.sleep(1.2)

        # Ocultar loader rápidamente si aún está visible
        page.evaluate("() => { const l = document.getElementById('loader'); if (l) l.style.display = 'none'; }")

        print("--- ESCENA 1: Portal de Acceso Privado (Foto 4: Reloj en vivo, Logo 3D y Botones) ---")
        time.sleep(2.5)

        print("--- ESCENA 2: Desbloqueo VIP con Clave (Solicitud y Validación) ---")
        page.click("#gatewayEnterBtn")
        time.sleep(1.2)
        page.fill("#vipRequestEmail", "vip@solariluxury.com")
        page.click("button:has-text('ENVIAR KEY')")
        time.sleep(1.5)
        page.click("button:has-text('DESBLOQUEAR TIENDA')")
        time.sleep(2.2)

        print("--- ESCENA 3: Hero Cinemático con Ticker Tape Árabe y Frases Central Cee ---")
        time.sleep(2.8)

        print("--- ESCENA 4: Transición al Mundo Blanco & Manifiesto Cinético Apple ---")
        # Scroll suave hacia el manifesto
        page.evaluate("() => window.smoothScrollTo(4200, 2400)")
        time.sleep(2.8)

        print("--- ESCENA 5: Bestseller Rotativo Dinámico ---")
        page.evaluate("() => { const el = document.getElementById('featured'); if (el) window.smoothScrollTo(el.getBoundingClientRect().top + window.scrollY - 30, 1800); }")
        time.sleep(2.5)

        print("--- ESCENA 6: Catálogo Oficial y Apple Dynamic Island (Compacta) ---")
        page.evaluate("() => { const el = document.getElementById('shop'); if (el) window.smoothScrollTo(el.getBoundingClientRect().top + window.scrollY - 20, 1800); }")
        time.sleep(2.5)

        print("--- ESCENA 7: Despliegue de la Dynamic Island y Filtrado ---")
        page.click("#adiActiveCatBtn")
        time.sleep(1.8)
        # Seleccionar categoría
        chip = page.locator(".adi-cat-chip:has-text('Calzado / Sneakers')")
        if chip.count() > 0:
            chip.click()
            time.sleep(1.5)

        # Restaurar a TODOS
        chip_all = page.locator(".adi-cat-chip:has-text('TODOS')")
        if chip_all.count() > 0:
            chip_all.click()
            time.sleep(1.2)

        # Cerrar Dynamic Island
        page.click("#adiActiveCatBtn")
        time.sleep(0.8)

        print("--- ESCENA 8: Hotbar Estático Parqueado (No sigue al usuario en el catálogo) ---")
        page.evaluate("() => window.smoothScrollBy(900, 2000)")
        time.sleep(2.5)
        page.evaluate("() => window.smoothScrollBy(900, 2000)")
        time.sleep(2.5)

        print("--- ESCENA 9: Retorno suave hacia arriba (El hotbar se re-acopla) ---")
        page.evaluate("() => window.smoothScrollTo(7200, 1800)")
        time.sleep(1.8)

        page_video = page.video
        context.close()
        browser.close()

        recorded_path = page_video.path()
        print(f"[3/4] Video capturado: {recorded_path}")

    # Transcodificar con FFmpeg
    target_mp4 = os.path.join(CAPS_DIR, "solariluxury_showcase_whatsapp.mp4")
    target_mp4_alt = os.path.join(CAP_DIR, "solariluxury_showcase_whatsapp.mp4")

    print("[4/4] Transcodificando a MP4 WhatsApp compatible...")
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", recorded_path,
        "-c:v", "libx264",
        "-profile:v", "main",
        "-level", "3.1",
        "-preset", "medium",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-movflags", "+faststart",
        target_mp4
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        file_size_mb = os.path.getsize(target_mp4) / (1024 * 1024)
        print(f"[OK] Video generado: {target_mp4} ({file_size_mb:.2f} MB)")
        shutil.copy2(target_mp4, target_mp4_alt)
        print(f"[OK] Copia lista en: {target_mp4_alt}")
    else:
        print(f"[ERROR]: {res.stderr}")

if __name__ == "__main__":
    record()
