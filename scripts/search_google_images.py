import asyncio
import urllib.parse
from playwright.async_api import async_playwright

async def search_google_images():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        queries = [
            ("Trapstar Decoded Puffer Black", "puffer"),
            ("Trapstar Shooters Tracksuit Grey", "tracksuit"),
            ("Trapstar 3M Reflective jacket", "3m"),
            ("Central Cee Trapstar London photoshoot", "ccee_trapstar"),
            ("Central Cee street style photoshoot", "ccee_street")
        ]
        
        for q, label in queries:
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}&tbm=isch"
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
                
                # accept cookies if modal
                try:
                    btn = await page.query_selector('button:has-text("Aceptar"), button:has-text("Accept all"), button:has-text("I agree")')
                    if btn: await btn.click()
                except: pass
                
                # extract images
                imgs = await page.evaluate('''() => {
                    const results = [];
                    const imgEls = document.querySelectorAll('div[data-ved] img');
                    for (let img of imgEls) {
                        const src = img.src || img.getAttribute('data-src');
                        const alt = img.alt || '';
                        if (src && src.startsWith('http') && !src.includes('gstatic.com') && !src.includes('google.com')) {
                            results.push({ src, alt });
                        }
                    }
                    return results.slice(0, 5);
                }''')
                print(f"=== Google Images for {q} ===")
                for im in imgs:
                    print(" ", im['alt'][:40], "->", im['src'][:80])
            except Exception as e:
                print(f"Error {q}: {e}")
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(search_google_images())
