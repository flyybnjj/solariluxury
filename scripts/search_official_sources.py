import asyncio
import urllib.parse
from playwright.async_api import async_playwright

async def search_trapstar_official():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        
        queries = [
            "site:uk.trapstarlondon.com Decoded Puffer",
            "site:uk.trapstarlondon.com Shooters Tracksuit",
            "site:uk.trapstarlondon.com Chenille",
            "site:uk.trapstarlondon.com Hyperdrive",
            "site:nosaucetheplug.com Trapstar Decoded Puffer",
            "site:nosaucetheplug.com Trapstar Shooters Tracksuit",
            "site:thefashionisto.com Central Cee",
            "Central Cee British GQ photoshoot",
            "Central Cee Trapstar London"
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
    asyncio.run(search_trapstar_official())
