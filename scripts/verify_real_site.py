import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\avalo\.gemini\antigravity\brain\23516fd4-d36b-4594-88ec-e2455796c906"

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1440, 'height': 900})
        page = await context.new_page()
        
        # 1. Load Homepage
        print("Navigating to http://127.0.0.1:8000/ ...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1000)
        
        # Screenshot Hero (Phase 1: Real Central Cee Portrait)
        p1_path = os.path.join(ARTIFACT_DIR, "preview_real_hero_central_cee.png")
        await page.screenshot(path=p1_path)
        print(f"Captured: {p1_path}")
        
        # 2. Scroll to Phase 2/3 (Middle of scroll: ~60% down the pinned container)
        container = await page.query_selector('#experiencePin')
        box = await container.bounding_box()
        # Scroll down ~1800px into Phase 3
        await page.evaluate("window.scrollTo(0, 1800)")
        await page.wait_for_timeout(1200)
        
        p3_path = os.path.join(ARTIFACT_DIR, "preview_real_stage_puffer.png")
        await page.screenshot(path=p3_path)
        print(f"Captured: {p3_path}")
        
        # 3. Test HUD button [02] 3M Reflective Flash
        btn_3m = await page.query_selector('#hudBtnReflective')
        if btn_3m:
            await btn_3m.click()
            await page.wait_for_timeout(600)
            p3m_path = os.path.join(ARTIFACT_DIR, "preview_real_3m_flash.png")
            await page.screenshot(path=p3m_path)
            print(f"Captured: {p3m_path}")
            
        # 4. Test HUD button [03] Chenille Macro
        btn_chenille = await page.query_selector('#hudBtnChenille')
        if btn_chenille:
            await btn_chenille.click()
            await page.wait_for_timeout(600)
            p_chenille_path = os.path.join(ARTIFACT_DIR, "preview_real_chenille_macro.png")
            await page.screenshot(path=p_chenille_path)
            print(f"Captured: {p_chenille_path}")
            
        # 5. Open Shopping Bag Drawer
        bag_btn = await page.query_selector('#bagBtn')
        if bag_btn:
            await bag_btn.click()
            await page.wait_for_timeout(600)
            p_cart_path = os.path.join(ARTIFACT_DIR, "preview_real_cart_drawer.png")
            await page.screenshot(path=p_cart_path)
            print(f"Captured: {p_cart_path}")
            
            # Close drawer
            close_btn = await page.query_selector('#cartCloseBtn')
            if close_btn: await close_btn.click()
            await page.wait_for_timeout(400)
            
        # 6. Scroll down to catalog
        await page.evaluate("document.getElementById('shop-catalog').scrollIntoView()")
        await page.wait_for_timeout(800)
        p_catalog_path = os.path.join(ARTIFACT_DIR, "preview_real_catalog.png")
        await page.screenshot(path=p_catalog_path)
        print(f"Captured: {p_catalog_path}")
        
        # 7. Check Central Cee Archive Quote Modal
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(600)
        quote_btn = await page.query_selector('#ccQuoteBtn')
        if quote_btn:
            await quote_btn.click()
            await page.wait_for_timeout(600)
            p_quote_path = os.path.join(ARTIFACT_DIR, "preview_real_cc_archive.png")
            await page.screenshot(path=p_quote_path)
            print(f"Captured: {p_quote_path}")

        await browser.close()
        print("Verification complete!")

if __name__ == '__main__':
    asyncio.run(verify())
