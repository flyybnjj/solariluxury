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

        print("Navegando a http://127.0.0.1:8000/...")
        page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2.0)

        # Ensure loader is gone
        page.evaluate("() => { const l = document.getElementById('loader'); if (l) l.style.display = 'none'; }")
        time.sleep(0.5)

        # 1. Hero pin desktop (dark cinematic video)
        hero_cap = os.path.join(CAPS_DIR, "01_home_hero_desktop.png")
        page.screenshot(path=hero_cap)
        print(f"[OK] Captura guardada: {hero_cap}")

        # 2. Scroll to Manifesto / Campaign section (white background starts here)
        page.evaluate("() => window.scrollTo(0, 4800)")
        time.sleep(1.0)
        manif_cap = os.path.join(CAPS_DIR, "15_transicion_fondo_blanco_manifesto.png")
        page.screenshot(path=manif_cap)
        print(f"[OK] Captura guardada: {manif_cap}")

        # 3. Scroll to Featured Product (Dynamic Bestseller Showcase on pure white background)
        page.evaluate("() => { const el = document.getElementById('featured'); if (el) { const y = el.getBoundingClientRect().top + window.pageYOffset - 85; window.scrollTo({top: y, behavior: 'instant'}); } }")
        time.sleep(1.2)
        featured_cap = os.path.join(CAPS_DIR, "16_featured_puffer_fondo_blanco.png")
        page.screenshot(path=featured_cap)
        print(f"[OK] Captura guardada: {featured_cap}")

        # 4. Scroll to Catalog (Luxury Vault on pure white background)
        page.evaluate("() => { const el = document.getElementById('shop'); if (el) { const y = el.getBoundingClientRect().top + window.pageYOffset - 85; window.scrollTo({top: y, behavior: 'instant'}); } }")
        time.sleep(1.2)
        cat_cap = os.path.join(CAPS_DIR, "02_catalogo_vault_alineacion.png")
        page.screenshot(path=cat_cap)
        print(f"[OK] Captura guardada: {cat_cap}")

        cat_white_cap = os.path.join(CAPS_DIR, "17_catalogo_completo_fondo_blanco.png")
        page.screenshot(path=cat_white_cap)
        print(f"[OK] Captura guardada: {cat_white_cap}")

        # 5. Hover on product card (shows animated moving red neon border)
        first_card = page.locator(".prod-card").first
        if first_card.count() > 0:
            first_card.hover()
            time.sleep(0.8)
            hover_cap = os.path.join(CAPS_DIR, "03_catalogo_tarjeta_hover.png")
            page.screenshot(path=hover_cap)
            print(f"[OK] Captura guardada: {hover_cap}")

        # 6. Find 360 spin sneaker card
        card_360 = page.locator(".prod-card[data-is-360='true']").first
        if card_360.count() > 0:
            card_360.scroll_into_view_if_needed()
            card_360.hover()
            time.sleep(0.6)
            spin_cap = os.path.join(CAPS_DIR, "04_catalogo_calzado_sneakers_360.png")
            page.screenshot(path=spin_cap)
            print(f"[OK] Captura guardada: {spin_cap}")

            # Quick View Modal on pure white theme
            qv_btn = card_360.locator(".pc-quickview-btn")
            if qv_btn.count() > 0:
                qv_btn.click()
                time.sleep(0.8)
                modal_cap = os.path.join(CAPS_DIR, "05_catalogo_modal_quickview.png")
                page.screenshot(path=modal_cap)
                print(f"[OK] Captura guardada: {modal_cap}")
                # Close modal
                page.keyboard.press("Escape")
                time.sleep(0.5)

        # 7. Mobile View on white background
        mobile_context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True)
        mobile_page = mobile_context.new_page()
        mobile_page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded", timeout=15000)
        mobile_page.evaluate("() => { const l = document.getElementById('loader'); if (l) l.style.display = 'none'; }")
        mobile_page.evaluate("() => { const el = document.getElementById('shop'); if (el) el.scrollIntoView(); }")
        time.sleep(1.0)
        mob_cap = os.path.join(CAPS_DIR, "13_movil_catalogo_grilla.png")
        mobile_page.screenshot(path=mob_cap)
        print(f"[OK] Captura guardada: {mob_cap}")

        browser.close()
        print("¡Todas las capturas con fondo blanco generadas con éxito!")

if __name__ == "__main__":
    run()
