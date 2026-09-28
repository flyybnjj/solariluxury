import sys
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    # 1. Inspect productos at 360px
    print("=== INSPECTING PRODUCTOS AT 360px ===")
    page = browser.new_page(viewport={'width': 360, 'height': 800})
    page.goto('http://127.0.0.1:8000/productos/', wait_until='domcontentloaded')
    page.wait_for_timeout(500)
    culprits = page.evaluate("""() => {
        const win = window.innerWidth;
        const res = [];
        document.querySelectorAll('*').forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.right > win + 1 || rect.width > win + 1) {
                res.push({
                    tag: el.tagName,
                    id: el.id,
                    className: (typeof el.className === 'string' ? el.className.slice(0, 80) : ''),
                    width: Math.round(rect.width),
                    left: Math.round(rect.left),
                    right: Math.round(rect.right),
                    parentTag: el.parentElement ? el.parentElement.tagName : '',
                    parentId: el.parentElement ? el.parentElement.id : '',
                    parentClass: el.parentElement && typeof el.parentElement.className === 'string' ? el.parentElement.className.slice(0, 80) : ''
                });
            }
        });
        return res;
    }""")
    print(f"Total elements with width/right > 360px: {len(culprits)}")
    for c in culprits[:15]:
        print(f"  <{c['tag']} id='{c['id']}' class='{c['className']}'> w={c['width']}, left={c['left']}, right={c['right']} (parent <{c['parentTag']} id='{c['parentId']}' class='{c['parentClass']}'>)")
    page.close()
    
    # 2. Inspect informacion at 320px
    print("\n=== INSPECTING INFORMACION AT 320px ===")
    page = browser.new_page(viewport={'width': 320, 'height': 800})
    page.goto('http://127.0.0.1:8000/locales/informacion/', wait_until='domcontentloaded')
    page.wait_for_timeout(500)
    culprits2 = page.evaluate("""() => {
        const win = window.innerWidth;
        const res = [];
        document.querySelectorAll('*').forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.right > win + 1 || rect.width > win + 1) {
                res.push({
                    tag: el.tagName,
                    id: el.id,
                    className: (typeof el.className === 'string' ? el.className.slice(0, 80) : ''),
                    width: Math.round(rect.width),
                    left: Math.round(rect.left),
                    right: Math.round(rect.right),
                    parentTag: el.parentElement ? el.parentElement.tagName : '',
                    parentId: el.parentElement ? el.parentElement.id : '',
                    parentClass: el.parentElement && typeof el.parentElement.className === 'string' ? el.parentElement.className.slice(0, 80) : ''
                });
            }
        });
        return res;
    }""")
    print(f"Total elements with width/right > 320px: {len(culprits2)}")
    for c in culprits2[:15]:
        print(f"  <{c['tag']} id='{c['id']}' class='{c['className']}'> w={c['width']}, left={c['left']}, right={c['right']} (parent <{c['parentTag']} id='{c['parentId']}' class='{c['parentClass']}'>)")
    page.close()
    
    browser.close()
