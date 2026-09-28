import asyncio
from playwright.async_api import async_playwright

async def inspect_google():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        url = "https://www.google.com/search?q=Trapstar+Decoded+Puffer+jacket+black&tbm=isch"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        
        # reject or accept cookies if any
        try:
            btn = await page.query_selector('button:has-text("Aceptar todo"), button:has-text("Accept all"), button:has-text("I agree")')
            if btn: await btn.click()
        except: pass
        
        # find image thumbnails
        thumbs = await page.query_selector_all('div[data-ved] img')
        print(f"Found {len(thumbs)} thumbnails")
        
        # click first 3 thumbnails and wait for large preview
        for i in range(min(5, len(thumbs))):
            try:
                await thumbs[i].click()
                await page.wait_for_timeout(1500)
                
                # In side panel, the large image is usually in an a tag or img with specific attributes
                large_img = await page.evaluate('''() => {
                    const imgs = document.querySelectorAll('img[src^="http"]');
                    for (let img of imgs) {
                        if (img.naturalWidth > 300 && !img.src.includes('google.com') && !img.src.includes('gstatic.com')) {
                            return { src: img.src, w: img.naturalWidth, h: img.naturalHeight };
                        }
                    }
                    return null;
                }''')
                if large_img:
                    print(f"  Result {i}: {large_img['src']} ({large_img['w']}x{large_img['h']})")
                else:
                    # check if any gstatic image is large
                    src = await thumbs[i].get_attribute('src')
                    print(f"  Thumb {i}: {src[:60] if src else 'no src'}")
            except Exception as e:
                print(f"  Error on thumb {i}: {e}")
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_google())
