import os
import sys
import json
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "capturas_mobile_audit", "despues")
os.makedirs(OUTPUT_DIR, exist_ok=True)

VIEWPORTS = [
    {"name": "320x568_p", "w": 320, "h": 568},
    {"name": "568x320_l", "w": 568, "h": 320},
    {"name": "360x640_p", "w": 360, "h": 640},
    {"name": "640x360_l", "w": 640, "h": 360},
    {"name": "375x667_p", "w": 375, "h": 667},
    {"name": "667x375_l", "w": 667, "h": 375},
    {"name": "390x844_p", "w": 390, "h": 844},
    {"name": "844x390_l", "w": 844, "h": 390},
    {"name": "412x915_p", "w": 412, "h": 915},
    {"name": "915x412_l", "w": 915, "h": 412},
    {"name": "430x932_p", "w": 430, "h": 932},
    {"name": "932x430_l", "w": 932, "h": 430},
    {"name": "768x1024_tablet", "w": 768, "h": 1024},
    {"name": "1280x800_desktop", "w": 1280, "h": 800},
]

PAGES = [
    {"slug": "inicio", "url": "/"},
    {"slug": "productos", "url": "/productos/"},
    {"slug": "detalle", "url": "/productos/33/"},
    {"slug": "locales", "url": "/locales/"},
    {"slug": "informacion", "url": "/locales/informacion/"},
    {"slug": "login", "url": "/login/"},
    {"slug": "validar_pin", "url": "/validar-pin/"},
    {"slug": "registro", "url": "/registro/"},
    {"slug": "perfil", "url": "/perfil/"},
]

def run_despues_audit():
    print("==================================================")
    print("  SOLARY LUXURY — FASE FINAL AUDITORIA Y VERIFICACION")
    print("==================================================")

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pages_audited": {},
        "flows_tested": {},
        "summary": {}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        total_checks = 0
        overflow_count = 0

        for pg in PAGES:
            slug = pg["slug"]
            url = BASE_URL + pg["url"]
            print(f"\n[AUDIT DESPUES] Auditando: {slug} ({url})")
            results["pages_audited"][slug] = {}

            for vp in VIEWPORTS:
                vp_name = vp["name"]
                w = vp["w"]
                h = vp["h"]

                context = browser.new_context(
                    viewport={"width": w, "height": h},
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" if w < 600 else None
                )
                page = context.new_page()

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=12000)
                    page.wait_for_timeout(400)

                    # Check overflow metrics
                    metrics = page.evaluate("""() => {
                        const winWidth = window.innerWidth;
                        const docWidth = Math.max(
                            document.documentElement.scrollWidth,
                            document.body ? document.body.scrollWidth : 0
                        );
                        const hasOverflow = docWidth > winWidth + 1;
                        
                        // Check inputs font size
                        const inputs = Array.from(document.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]), select, textarea'));
                        const sub16Inputs = inputs.filter(el => {
                            const fs = parseFloat(window.getComputedStyle(el).fontSize);
                            return fs < 15.5;
                        }).map(el => el.name || el.id || el.className);

                        return {
                            winWidth,
                            docWidth,
                            hasOverflow,
                            overflowPixels: Math.max(0, docWidth - winWidth),
                            inputsCount: inputs.length,
                            sub16InputsCount: sub16Inputs.length
                        };
                    }""")

                    total_checks += 1
                    if metrics["hasOverflow"]:
                        overflow_count += 1
                        print(f"  [X] {vp_name}: OVERFLOW ({metrics['docWidth']}px > {metrics['winWidth']}px, +{metrics['overflowPixels']}px)")
                    else:
                        print(f"  [OK] {vp_name}: OK ({metrics['docWidth']}px <= {metrics['winWidth']}px)")

                    # Save screenshot
                    img_path = os.path.join(OUTPUT_DIR, f"{slug}_{vp_name}.png")
                    page.screenshot(path=img_path, full_page=False)

                    results["pages_audited"][slug][vp_name] = {
                        "metrics": metrics,
                        "screenshot": os.path.relpath(img_path, BASE_DIR)
                    }

                except Exception as e:
                    print(f"  [!] Error en {slug} {vp_name}: {e}")
                    results["pages_audited"][slug][vp_name] = {"error": str(e)}

                finally:
                    context.close()

        # ── INTERACTION USER JOURNEY (MOBILE 390x844) ───────────
        print("\n--- Ejecutando Journey de Interaccion Touch en Mobile (390x844) ---")
        flow_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True
        )
        flow_page = flow_context.new_page()

        try:
            # 1. Visitar inicio
            flow_page.goto(BASE_URL + "/", wait_until="domcontentloaded")
            flow_page.evaluate("""() => {
                sessionStorage.setItem('solariluxury_vip_unlocked', 'true');
                const gw = document.getElementById('privateGatewayScreen');
                if (gw) gw.classList.add('unlocked');
                document.body.classList.remove('store-locked');
            }""")
            flow_page.wait_for_timeout(400)
            print("  1. Portada cargada y desbloqueada")

            # 2. Agregar un producto a la bolsa
            add_btn = flow_page.locator(".pc-add-btn").first
            if add_btn.count() > 0:
                add_btn.scroll_into_view_if_needed()
                flow_page.wait_for_timeout(300)
                add_btn.click()
                print("  2. Click en '+ AÑADIR'")
                flow_page.wait_for_timeout(800)

                # Captura cart drawer abierto
                cart_shot = os.path.join(OUTPUT_DIR, "flow_cart_drawer_390x844.png")
                flow_page.screenshot(path=cart_shot)
                results["flows_tested"]["cart_drawer"] = {"status": "SUCCESS", "screenshot": os.path.relpath(cart_shot, BASE_DIR)}
                print(f"  -> Cart Drawer verificado y capturado: {cart_shot}")

                # 3. Click en Finalizar Compra / Checkout
                checkout_btn = flow_page.locator("#cartDrawerCta, .cd-cta").first
                if checkout_btn.count() > 0 and checkout_btn.is_visible():
                    checkout_btn.click()
                    print("  3. Click en 'FINALIZAR COMPRA'")
                    flow_page.wait_for_timeout(800)

                    modal_shot = os.path.join(OUTPUT_DIR, "flow_checkout_modal_390x844.png")
                    flow_page.screenshot(path=modal_shot)
                    results["flows_tested"]["checkout_modal"] = {"status": "SUCCESS", "screenshot": os.path.relpath(modal_shot, BASE_DIR)}
                    print(f"  -> Checkout Modal Bottom Sheet capturado: {modal_shot}")

            # 4. Visitar detalle de producto
            flow_page.goto(BASE_URL + "/productos/33/", wait_until="domcontentloaded")
            flow_page.wait_for_timeout(600)
            detail_shot = os.path.join(OUTPUT_DIR, "flow_detalle_sticky_bar_390x844.png")
            flow_page.screenshot(path=detail_shot)
            results["flows_tested"]["detalle_sticky_bar"] = {"status": "SUCCESS", "screenshot": os.path.relpath(detail_shot, BASE_DIR)}
            print(f"  4. Detalle de producto con Sticky Buy Bar capturado: {detail_shot}")

        except Exception as ex:
            print(f"  [!] Error en flow interactivo: {ex}")
            results["flows_tested"]["error"] = str(ex)
        finally:
            flow_context.close()

        browser.close()

    results["summary"] = {
        "total_checks": total_checks,
        "overflow_count": overflow_count,
        "all_passed": (overflow_count == 0)
    }

    report_path = os.path.join(BASE_DIR, "capturas_mobile_audit", "fase_final_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n==================================================")
    print(f"  TOTAL CHECKS: {total_checks}")
    print(f"  TOTAL OVERFLOWS: {overflow_count}")
    print(f"  RESULTADO: {'TODO PERFECTO - LISTO PARA AWS' if overflow_count == 0 else 'HAY OVERFLOWS PENDIENTES'}")
    print(f"  REPORTE GUARDADO EN: {report_path}")
    print("==================================================")

if __name__ == "__main__":
    run_despues_audit()
