import asyncio
import urllib.parse
from playwright.async_api import async_playwright

async def find_tracksuit_and_reflective():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        
        queries = [
            "Trapstar Shooters Tracksuit grey site:depop.com",
            "Trapstar Shooters Tracksuit grey site:grailed.com",
            "Trapstar Decoded Puffer 3M reflective site:depop.com",
            "Trapstar Hyperdrive puffer jacket black site:depop.com",
            "Central Cee Trapstar London outfit",
            "Central Cee Syna World tracksuit photoshoot",
            "Trapstar chenille badge logo macro"
        ]
        
        for q in queries:
            url = f"https://www.bing.com/images/search?q={urllib.parse.quote_plus(q)}&first=1"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1500)
            
            items = await page.evaluate('''() => {
                const res = [];
                const els = document.querySelectorAll('a.iusc');
                for (let el of els) {
                    try {
                        const m = JSON.parse(el.getAttribute('m'));
                        if (m && m.murl) {
                            res.push({ url: m.murl, title: m.t || '' });
                        }
                    } catch(e) {}
                }
                return res.slice(0, 4);
            }''')
            print(f"=== {q} ===")
            for it in items:
                print(f"  {it['title'][:45]} -> {it['url']}")
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(find_tracksuit_and_reflective())
