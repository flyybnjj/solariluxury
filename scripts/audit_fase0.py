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
OUTPUT_DIR = os.path.join(BASE_DIR, "capturas_mobile_audit", "antes")
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
    {"slug": "login_password", "url": "/login-password/"},
    {"slug": "perfil", "url": "/perfil/"},
]

def check_viewport_meta():
    meta_audit = {}
    templates_dir = os.path.join(BASE_DIR, "mi_proyecto")
    for root, dirs, files in os.walk(templates_dir):
        for f in files:
            if f.endswith('.html'):
                p = os.path.join(root, f)
                rel = os.path.relpath(p, BASE_DIR)
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                        txt = fp.read()
                        has_meta = 'name="viewport"' in txt or "name='viewport'" in txt
                        has_cover = 'viewport-fit=cover' in txt
                        meta_audit[rel] = {
                            "has_viewport_meta": has_meta,
                            "has_viewport_fit_cover": has_cover
                        }
                except Exception:
                    pass
    return meta_audit

def check_overflow(page):
    return page.evaluate("""
        () => {
            const winW = window.innerWidth;
            const docW = document.documentElement.scrollWidth;
            const bodyW = document.body ? document.body.scrollWidth : 0;
            const maxW = Math.max(docW, bodyW);
            const overflowing = [];
            
            if (maxW > winW + 1) {
                const elements = document.querySelectorAll('*');
                elements.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.right > winW + 1 || rect.left < -1) {
                        overflowing.push({
                            tag: el.tagName,
                            id: el.id,
                            className: (typeof el.className === 'string' ? el.className.slice(0, 100) : ''),
                            width: Math.round(rect.width),
                            left: Math.round(rect.left),
                            right: Math.round(rect.right),
                            scrollWidth: el.scrollWidth
                        });
                    }
                });
            }
            return {
                winW: winW,
                scrollW: maxW,
                hasOverflow: maxW > winW + 1,
                overflowingCount: overflowing.length,
                samples: overflowing.slice(0, 10)
            };
        }
    """)

def run_audit():
    print("=== INICIANDO AUDITORIA FASE 0 (PLAYWRIGHT) ===", flush=True)
    meta_results = check_viewport_meta()
    
    results = {
        "viewport_meta": meta_results,
        "pages": {}
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for page_info in PAGES:
            slug = page_info["slug"]
            url = BASE_URL + page_info["url"]
            results["pages"][slug] = {}
            print(f"\n[PAGE] {slug} ({url})", flush=True)
            
            for vp in VIEWPORTS:
                context = browser.new_context(viewport={"width": vp["w"], "height": vp["h"]})
                page = context.new_page()
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    page.wait_for_timeout(800)
                    
                    ov = check_overflow(page)
                    results["pages"][slug][vp["name"]] = ov
                    
                    img_path = os.path.join(OUTPUT_DIR, f"{slug}_{vp['name']}.png")
                    page.screenshot(path=img_path, full_page=False)
                    
                    status = "[OVERFLOW]" if ov["hasOverflow"] else "[OK]"
                    print(f"  {vp['name']:<18} | {status} | Win: {ov['winW']}px | Doc: {ov['scrollW']}px | Elementos desbordados: {ov['overflowingCount']}", flush=True)
                except Exception as e:
                    print(f"  {vp['name']:<18} | ERROR: {e}", flush=True)
                    results["pages"][slug][vp["name"]] = {"error": str(e)}
                finally:
                    context.close()
                    
        # Modales y Drawers en inicio
        print("\n[MODALES & DRAWERS EN INICIO]", flush=True)
        for vp_name, w, h in [("390x844_p", 390, 844), ("1280x800_desktop", 1280, 800)]:
            context = browser.new_context(viewport={"width": w, "height": h})
            page = context.new_page()
            try:
                page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=10000)
                page.wait_for_timeout(1000)
                
                # 1. Drawer Carrito
                page.evaluate("() => { if (typeof openCart === 'function') openCart(); else if (typeof openGlobalCart === 'function') openGlobalCart(); }")
                page.wait_for_timeout(600)
                cart_ov = check_overflow(page)
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"modal_cart_{vp_name}.png"))
                print(f"  Drawer Carrito ({vp_name}): {'[OVERFLOW]' if cart_ov['hasOverflow'] else '[OK]'} (Doc: {cart_ov['scrollW']}px)", flush=True)
                page.evaluate("() => { if (typeof closeCart === 'function') closeCart(); }")
                page.wait_for_timeout(400)
                
                # 2. Drawer Wishlist
                page.evaluate("() => { if (typeof openWishlist === 'function') openWishlist(); else if (typeof openGlobalWishlist === 'function') openGlobalWishlist(); }")
                page.wait_for_timeout(600)
                wish_ov = check_overflow(page)
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"modal_wishlist_{vp_name}.png"))
                print(f"  Drawer Wishlist ({vp_name}): {'[OVERFLOW]' if wish_ov['hasOverflow'] else '[OK]'} (Doc: {wish_ov['scrollW']}px)", flush=True)
                page.evaluate("() => { if (typeof closeWishlist === 'function') closeWishlist(); }")
                page.wait_for_timeout(400)
                
                # 3. Modal Checkout
                page.evaluate("() => { if (typeof openCheckoutModal === 'function') openCheckoutModal(); else if (typeof openGlobalCheckoutModal === 'function') openGlobalCheckoutModal(); }")
                page.wait_for_timeout(600)
                chk_ov = check_overflow(page)
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"modal_checkout_{vp_name}.png"))
                print(f"  Modal Checkout ({vp_name}): {'[OVERFLOW]' if chk_ov['hasOverflow'] else '[OK]'} (Doc: {chk_ov['scrollW']}px)", flush=True)
                page.evaluate("() => { if (typeof closeCheckoutModal === 'function') closeCheckoutModal(); }")
                page.wait_for_timeout(400)
                
                # 4. Modal VIP
                page.evaluate("() => { const m = document.getElementById('vipModal'); if (m) m.classList.add('active'); }")
                page.wait_for_timeout(600)
                vip_ov = check_overflow(page)
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"modal_vip_{vp_name}.png"))
                print(f"  Modal VIP ({vp_name}): {'[OVERFLOW]' if vip_ov['hasOverflow'] else '[OK]'} (Doc: {vip_ov['scrollW']}px)", flush=True)
            finally:
                context.close()
                
        browser.close()
        
    report_file = os.path.join(BASE_DIR, "capturas_mobile_audit", "fase0_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[AUDITORIA COMPLETADA] Reporte guardado en {report_file}", flush=True)

if __name__ == "__main__":
    run_audit()
