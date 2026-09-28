import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # iPhone 14/15 size: 390x844
        context = await browser.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        page = await context.new_page()

        # Unlock store session
        await page.add_init_script("""
            sessionStorage.setItem('solariluxury_vip_unlocked', 'true');
        """)

        print("Navigating to http://127.0.0.1:8000/ ...")
        await page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        os.makedirs("test_reports/user_fixes", exist_ok=True)

        # 1. TEST HERO SECTION
        print("\n--- TEST 1: HERO TITLE ---")
        hero = page.locator("#heroSection, #heroPin")
        hero_brand = page.locator(".hero-brand-solar")
        hero_artist = page.locator(".hero-collab-artist")
        hero_cross = page.locator(".hero-collab-cross")

        print("Hero brand text:", await hero_brand.text_content())
        print("Hero artist text:", await hero_artist.text_content())
        print("Hero cross text:", await hero_cross.text_content())
        assert "SOLARILUXURY" in (await hero_brand.text_content())
        assert "CENTRAL CEE" in (await hero_artist.text_content())

        await page.screenshot(path="test_reports/user_fixes/01_hero_mobile.png")
        print("[OK] Hero screenshot captured: test_reports/user_fixes/01_hero_mobile.png")

        # 2. TEST MANIFESTO SECTION
        print("\n--- TEST 2: MANIFESTO WORDS ---")
        manifesto = page.locator("#manifestoText")
        await manifesto.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)

        em_elements = page.locator("#manifestoText em")
        count = await em_elements.count()
        print(f"Manifesto em tags found: {count}")
        for i in range(count):
            em_text = await em_elements.nth(i).text_content()
            em_color = await em_elements.nth(i).evaluate("el => window.getComputedStyle(el).color")
            em_vis = await em_elements.nth(i).evaluate("el => window.getComputedStyle(el).visibility")
            print(f"  em #{i+1}: text='{em_text}', color='{em_color}', vis='{em_vis}'")
            assert em_vis == "visible"

        await page.screenshot(path="test_reports/user_fixes/02_manifesto_mobile.png")
        print("[OK] Manifesto screenshot captured: test_reports/user_fixes/02_manifesto_mobile.png")

        # 3. TEST FEATURED BESTSELLER SECTION
        print("\n--- TEST 3: FEATURED BESTSELLER (PIEZA ESTRELLA) ---")
        featured = page.locator(".featured-card-wrap")
        await featured.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)

        grid_cols = await featured.evaluate("el => window.getComputedStyle(el).gridTemplateColumns")
        print(f"Featured gridTemplateColumns on 390px: {grid_cols}")
        cols_count = len(grid_cols.split())
        print(f"Number of columns: {cols_count}")
        assert cols_count == 1, f"Expected 1 column stack, got {cols_count}: {grid_cols}"

        feat_img = page.locator(".featured-hero-img")
        img_box = await feat_img.bounding_box()
        print(f"Featured image box: {img_box}")
        assert img_box and img_box['height'] > 50, "Featured image should have reasonable height"

        await page.screenshot(path="test_reports/user_fixes/03_featured_mobile.png")
        print("[OK] Featured bestseller screenshot captured: test_reports/user_fixes/03_featured_mobile.png")

        # 4. TEST SNEAKER QUICKVIEW 360 BAR
        print("\n--- TEST 4: SNEAKER QUICKVIEW 360 BAR ---")
        cards = page.locator(".prod-card")
        total_cards = await cards.count()
        print(f"Total product cards on page: {total_cards}")
        sneaker_card = None
        for i in range(total_cards):
            c = cards.nth(i)
            name = await c.get_attribute("data-name")
            gallery = await c.get_attribute("data-gallery")
            cat = await c.get_attribute("data-cat")
            if "jordan" in (name or "").lower() or (gallery and "|" in gallery and ("calzado" in (cat or "").lower() or "sneaker" in (cat or "").lower() or "zapatilla" in (cat or "").lower())):
                sneaker_card = c
                print(f"Found target sneaker card: {name} (gallery_count={len((gallery or '').split('|'))})")
                break
        if not sneaker_card:
            # fallback to any card with gallery
            for i in range(total_cards):
                c = cards.nth(i)
                gallery = await c.get_attribute("data-gallery")
                if gallery and "|" in gallery:
                    sneaker_card = c
                    print(f"Found card with gallery: {await c.get_attribute('data-name')}")
                    break

        await sneaker_card.scroll_into_view_if_needed()
        await page.wait_for_timeout(400)

        card_name = await sneaker_card.locator(".pc-name").text_content()
        print(f"Testing QuickView on card: {card_name.strip()}")

        qv_btn = sneaker_card.locator(".pc-quickview-btn")
        await qv_btn.click(force=True)
        await page.wait_for_timeout(600)

        qv_modal = page.locator("#quickViewModal")
        assert await qv_modal.is_visible(), "QuickView modal should be open"

        bar360 = page.locator("#qv360Bar")
        bar_display = await bar360.evaluate("el => window.getComputedStyle(el).display")
        print(f"360 bar display style: {bar_display}")
        assert bar_display == "block", f"Expected #qv360Bar display to be block, got {bar_display}"

        slider = page.locator("#qvStockxSlider")
        assert await slider.is_visible(), "StockX 360 slider should be visible"
        slider_max = await slider.get_attribute("max")
        slider_val = await slider.input_value()
        print(f"Slider max: {slider_max}, current val: {slider_val}")

        angle_text = page.locator("#qvAngleDeg")
        print("Initial angle text:", await angle_text.text_content())

        # Test scrub: change slider value
        await slider.fill("3")
        await page.wait_for_timeout(300)
        new_angle = await angle_text.text_content()
        print("Scrubbed angle text (slider=3):", new_angle)

        # Test auto spin toggle
        auto_spin_btn = page.locator("#qvAutoSpinBtn")
        await auto_spin_btn.click()
        await page.wait_for_timeout(700)
        auto_angle = await angle_text.text_content()
        print("Auto-spun angle text:", auto_angle)
        await auto_spin_btn.click() # Stop auto spin

        # Check modal image fit
        modal_img = page.locator("#qvModalImg")
        img_box = await modal_img.bounding_box()
        print(f"QuickView sneaker image box: width={img_box['width']}, height={img_box['height']}")
        assert img_box['width'] <= 360, "Sneaker image should not overflow modal width"

        await page.screenshot(path="test_reports/user_fixes/04_quickview_360_mobile.png")
        print("[OK] QuickView 360 screenshot captured: test_reports/user_fixes/04_quickview_360_mobile.png")

        await browser.close()
        print("\n================ ALL 4 USER FIXES VERIFIED SUCCESSFULLY ================")

if __name__ == "__main__":
    asyncio.run(run())
