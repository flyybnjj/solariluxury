import os
import time
from playwright.sync_api import sync_playwright

CAPS_DIR = r"C:\Users\avalo\Desktop\caps"
os.makedirs(CAPS_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        print("[1] Opening locked store gateway...")
        page.goto("http://127.0.0.1:8000/bloquear-tienda/")
        page.wait_for_timeout(1500)

        # Clear localStorage to ensure locked state
        page.evaluate("localStorage.removeItem('solariluxury_vip_unlocked');")
        page.reload()
        page.wait_for_timeout(1800)

        # 1. Capture Private Gateway Screen
        p1 = os.path.join(CAPS_DIR, "18_gateway_privado_vip.png")
        page.screenshot(path=p1)
        print(f"[OK] Saved {p1}")

        # 2. Open VIP Modal and request key
        print("[2] Opening VIP modal...")
        page.click("#gatewayEnterBtn")
        page.wait_for_timeout(600)

        # Type email to request key
        page.fill("#vipRequestEmail", "cench@solariluxury.com")
        page.click("button:has-text('ENVIAR KEY')")
        page.wait_for_timeout(1500)

        p2 = os.path.join(CAPS_DIR, "19_modal_vip_key_solicitud.png")
        page.screenshot(path=p2)
        print(f"[OK] Saved {p2}")

        # 3. Validate VIP key to unlock store
        print("[3] Validating VIP key...")
        page.click("button:has-text('DESBLOQUEAR TIENDA')")
        page.wait_for_timeout(1800)

        # 4. Capture Marquee Ticker with Arabic & Cench quotes
        print("[4] Capturing Marquee Arabic & Cench...")
        p3 = os.path.join(CAPS_DIR, "20_hero_marquee_arabe_cench.png")
        page.screenshot(path=p3)
        print(f"[OK] Saved {p3}")

        # 5. Scroll to Manifesto
        print("[5] Scrolling to Manifesto...")
        page.evaluate("document.getElementById('campaign').scrollIntoView({ behavior: 'smooth' });")
        page.wait_for_timeout(1200)
        p4 = os.path.join(CAPS_DIR, "21_manifesto_movimiento_apple.png")
        page.screenshot(path=p4)
        print(f"[OK] Saved {p4}")

        # 6. Scroll to Catalog & Apple Dynamic Island
        print("[6] Scrolling to Catalog Dynamic Island...")
        page.evaluate("document.getElementById('shop').scrollIntoView({ behavior: 'smooth' });")
        page.wait_for_timeout(1500)
        p5 = os.path.join(CAPS_DIR, "22_apple_dynamic_island_compact.png")
        page.screenshot(path=p5)
        print(f"[OK] Saved {p5}")

        # 7. Expand Apple Dynamic Island
        print("[7] Expanding Dynamic Island...")
        page.click("#adiActiveCatBtn")
        page.wait_for_timeout(800)
        p6 = os.path.join(CAPS_DIR, "23_apple_dynamic_island_expandida.png")
        page.screenshot(path=p6)
        print(f"[OK] Saved {p6}")

        # 8. Scroll deep into catalog to show parked hotbar
        print("[8] Scrolling deep into catalog to verify hotbar parking...")
        page.evaluate("window.scrollTo(0, document.getElementById('shop').offsetTop + 800);")
        page.wait_for_timeout(1200)
        p7 = os.path.join(CAPS_DIR, "24_hotbar_estatico_parqueado.png")
        page.screenshot(path=p7)
        print(f"[OK] Saved {p7}")

        browser.close()
        print("[ALL SCREENSHOTS CAPTURED SUCCESSFULLY]")

if __name__ == "__main__":
    run()
