from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_timeout(1000)
    page.evaluate("localStorage.setItem('solariluxury_vip_unlocked', 'true');")
    page.reload()
    page.wait_for_timeout(1000)

    # Calculate exact scroll needed to reach shop (where shopTop is 0)
    scroll_needed = page.evaluate("""() => {
        const shop = document.getElementById('shop');
        return shop.getBoundingClientRect().top + window.scrollY;
    }""")
    print("Exact shop document top:", scroll_needed)

    # 1. Scroll right to the entrance of shop (park threshold)
    page.evaluate(f"window.scrollTo(0, {scroll_needed});")
    page.wait_for_timeout(600)

    res1 = page.evaluate("""() => {
        const shop = document.getElementById('shop');
        const h = document.getElementById('siteHeader');
        return {
            scrollY: window.scrollY,
            shopTop: shop.getBoundingClientRect().top,
            headerPos: h.style.position,
            headerTop: h.style.top,
            headerRect: h.getBoundingClientRect()
        };
    }""")
    print("At shop entrance (parked):", res1)
    page.screenshot(path=r"C:\Users\avalo\Desktop\caps\24_hotbar_estatico_parqueado.png")

    # 2. Scroll 600px further down inside the 81 products
    page.evaluate(f"window.scrollTo(0, {scroll_needed + 700});")
    page.wait_for_timeout(600)
    res2 = page.evaluate("""() => {
        const shop = document.getElementById('shop');
        const h = document.getElementById('siteHeader');
        return {
            scrollY: window.scrollY,
            shopTop: shop.getBoundingClientRect().top,
            headerPos: h.style.position,
            headerTop: h.style.top,
            headerRect: h.getBoundingClientRect()
        };
    }""")
    print("700px down inside catalog (hotbar stayed up):", res2)
    page.screenshot(path=r"C:\Users\avalo\Desktop\caps\25_hotbar_no_sigue_al_usuario.png")

    browser.close()
