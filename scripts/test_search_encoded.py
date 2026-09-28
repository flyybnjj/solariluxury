import asyncio
import urllib.parse
from playwright.async_api import async_playwright

async def test_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        queries = [
            ("Central Cee Trapstar", "central_cee_trapstar"),
            ("Trapstar Decoded Puffer jacket black", "trapstar_puffer"),
            ("Trapstar Shooters Tracksuit grey", "trapstar_tracksuit"),
            ("Trapstar Decoded 3M reflective jacket", "trapstar_3m"),
            ("Trapstar chenille embroidery logo", "trapstar_chenille")
        ]
        
        for q, label in queries:
            encoded = urllib.parse.quote_plus(q)
            url = f"https://www.bing.com/images/search?q={encoded}&form=HDRSC2&first=1"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            
            items = await page.evaluate('''() => {
                const res = [];
                const els = document.querySelectorAll('a.iusc');
                for (let el of els) {
                    try {
                        const m = JSON.parse(el.getAttribute('m'));
                        if (m && m.murl) {
                            res.push({ url: m.murl, title: m.t || '', desc: m.desc || '' });
                        }
                    } catch(e) {}
                }
                return res.slice(0, 4);
            }''')
            print(f"=== Results for: {q} ===")
            for item in items:
                print(f"  {item['title']} -> {item['url']}")
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_search())
