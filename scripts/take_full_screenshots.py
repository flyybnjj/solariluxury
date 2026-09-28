import asyncio
import os
import shutil
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\avalo\.gemini\antigravity\brain\23516fd4-d36b-4594-88ec-e2455796c906"
PROJECT_DIR = r"C:\Users\avalo\Documents\tienda\capturas_sitio"
os.makedirs(PROJECT_DIR, exist_ok=True)

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Standard desktop view
        context = await browser.new_context(viewport={'width': 1440, 'height': 900})
        page = await context.new_page()

        async def save_shot(name, full_page=False):
            art_path = os.path.join(ARTIFACT_DIR, name)
            proj_path = os.path.join(PROJECT_DIR, name)
            await page.screenshot(path=art_path, full_page=full_page)
            shutil.copy2(art_path, proj_path)
            print(f"Captured: {name}")

        # ── 1. HOME HERO ──────────────────────────────────────────
        print("1. Loading Home...")
        await page.goto("http://127.0.0.1:8080/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)
        await save_shot("foto_01_home_hero.png")

        # ── 2. HOME INTERACTIVE STAGE ─────────────────────────────
        print("2. Home Stage...")
        await page.evaluate("window.scrollTo(0, 1800)")
        await page.wait_for_timeout(1200)
        await save_shot("foto_02_home_interactive_stage.png")

        # ── 3. HOME SHOP SECTION ──────────────────────────────────
        print("3. Home Catalog Section...")
        await page.evaluate("document.getElementById('shop-catalog') ? document.getElementById('shop-catalog').scrollIntoView() : window.scrollTo(0, 4200)")
        await page.wait_for_timeout(1000)
        await save_shot("foto_03_home_catalog_section.png")

        # ── 4. CATALOG / VAULT PAGE ───────────────────────────────
        print("4. Loading Catalog /productos/ ...")
        await page.goto("http://127.0.0.1:8080/productos/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)
        # Scroll down slightly to show filters & top of grid
        await page.evaluate("window.scrollTo(0, 150)")
        await page.wait_for_timeout(600)
        await save_shot("foto_04_catalogo_vault_filtros.png")

        # ── 5. QUICK VIEW MODAL (WITH REAL PACKSHOTS GALLERY) ─────
        print("5. Quick View Modal...")
        await page.evaluate("""() => {
            const card = document.querySelector(".prod-card[data-id='25']") || document.querySelector(".prod-card");
            if (card) {
                const btn = card.querySelector(".pc-quickview-btn");
                if (btn && typeof openQuickView === 'function') {
                    openQuickView(new MouseEvent('click'), btn);
                }
            }
        }""")
        await page.wait_for_timeout(900)
        await save_shot("foto_05_catalogo_quickview_modal.png")

        # Close modal
        await page.evaluate("() => { if (typeof closeQuickView === 'function') closeQuickView(); }")
        await page.wait_for_timeout(400)

        # ── 6. CATALOG ACTIVE FILTERS (SNEAKERS) ──────────────────
        print("6. Filtering by Sneakers...")
        await page.evaluate("""() => {
            const chip = document.querySelector(".cat-badge-chip[data-cat*='SNEAKERS']") || document.querySelector(".cat-badge-chip[data-cat*='ZAPATILLAS']");
            if (chip && typeof filterCatalogCategory === 'function') {
                filterCatalogCategory(chip.dataset.cat, chip);
            }
        }""")
        await page.wait_for_timeout(800)
        await save_shot("foto_06_catalogo_filtros_activos.png")

        # ── 6B. HOVER DUAL-IMAGE CROSSFADE ────────────────────────
        print("6B. Hover dual-image crossfade...")
        await page.evaluate("""() => {
            const visibleCards = Array.from(document.querySelectorAll('.prod-card-wrap')).filter(w => w.style.display !== 'none');
            if (visibleCards.length > 0) {
                const card = visibleCards[0].querySelector('.prod-card');
                if (card) {
                    const hoverImg = card.querySelector('.pc-img-hover');
                    if (hoverImg) {
                        hoverImg.style.opacity = '1';
                        hoverImg.style.transform = 'scale(1.06)';
                    }
                    const sizeBar = card.querySelector('.pc-size-bar');
                    if (sizeBar) {
                        sizeBar.style.transform = 'translateY(0)';
                        sizeBar.style.opacity = '1';
                    }
                    const qvBtn = card.querySelector('.pc-quickview-btn');
                    if (qvBtn) {
                        qvBtn.style.opacity = '1';
                        qvBtn.style.transform = 'translate(-50%, -50%) scale(1)';
                    }
                }
            }
        }""")
        await page.wait_for_timeout(600)
        await save_shot("foto_06b_catalogo_hover_crossfade.png")

        # ── 7. PRODUCT DETAIL: AIR JORDAN 4 BLACK CAT ─────────────
        print("7. Detail page: Jordan 4 Black Cat (/productos/25/)...")
        await page.goto("http://127.0.0.1:8080/productos/25/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)
        await save_shot("foto_07_detalle_jordan4_blackcat.png")

        # Scrolled detail view showing real thumbnails strip & related items
        await page.evaluate("window.scrollTo(0, 480)")
        await page.wait_for_timeout(600)
        await save_shot("foto_07b_detalle_jordan4_galeria_relacionados.png")

        # ── 8. PRODUCT DETAIL: PUFFER HYPERDRIVE ──────────────────
        print("8. Detail page: Puffer Hyperdrive (/productos/17/)...")
        await page.goto("http://127.0.0.1:8080/productos/17/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)
        await save_shot("foto_08_detalle_puffer_hyperdrive.png")

        # Scrolled view showing real 5 packshots & related items
        await page.evaluate("window.scrollTo(0, 480)")
        await page.wait_for_timeout(600)
        await save_shot("foto_08b_detalle_puffer_galeria_relacionados.png")

        # ── 9. STORES / LOCALES ───────────────────────────────────
        print("9. Stores page (/locales/)...")
        await page.goto("http://127.0.0.1:8080/locales/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)
        await save_shot("foto_09_sucursales_stores.png")

        # ── 10. LOGISTICS & RATE TRACKING ─────────────────────────
        print("10. Logistics page (/locales/informacion/)...")
        await page.goto("http://127.0.0.1:8080/locales/informacion/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)
        await save_shot("foto_10_logistica_y_cambio.png")

        # ── 11. APPLE PANEL DROPDOWN ──────────────────────────────
        print("11. Panel Admin dropdown...")
        await page.evaluate("""() => {
            const btn = document.getElementById('subHeaderPanelBtn');
            if (btn && typeof toggleAppleTray === 'function') {
                toggleAppleTray('subHeaderPanelTray', btn);
            }
        }""")
        await page.wait_for_timeout(600)
        await save_shot("foto_11_panel_admin_apple_tray.png")

        await browser.close()
        print("All screenshots successfully captured!")

if __name__ == '__main__':
    asyncio.run(capture_all())
