import sys
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

test_pages = [
    ('productos', 'http://127.0.0.1:8000/productos/'),
    ('informacion', 'http://127.0.0.1:8000/locales/informacion/'),
    ('inicio', 'http://127.0.0.1:8000/'),
    ('detalle', 'http://127.0.0.1:8000/productos/33/'),
    ('login', 'http://127.0.0.1:8000/login/'),
    ('validar_pin', 'http://127.0.0.1:8000/validar-pin/'),
    ('solicitar_acceso', 'http://127.0.0.1:8000/solicitar-acceso/'),
    ('lista_locales', 'http://127.0.0.1:8000/locales/'),
    ('registro', 'http://127.0.0.1:8000/registro/'),
]

widths = [320, 360, 375, 390, 412, 430, 768, 1280]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    all_ok = True
    for slug, url in test_pages:
        print(f"\n--- Testing {slug} ---")
        for w in widths:
            page = browser.new_page(viewport={'width': w, 'height': 800})
            page.goto(url, wait_until='domcontentloaded')
            page.wait_for_timeout(400)
            res = page.evaluate("""() => {
                const win = window.innerWidth;
                const doc = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
                return { win: win, doc: doc, ok: doc <= win + 1 };
            }""")
            status = "[OK]" if res['ok'] else "[OVERFLOW]"
            if not res['ok']:
                all_ok = False
            print(f"  {w}px: {status} (win={res['win']}px, doc={res['doc']}px)")
            page.close()
    browser.close()
    print(f"\nOverall result: {'ALL PASSED' if all_ok else 'SOME OVERFLOWS REMAIN'}")
