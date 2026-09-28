import asyncio
import urllib.parse
from playwright.async_api import async_playwright

async def test_bing_queries():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        
        test_queries = [
            "Trapstar jacket",
            "Trapstar London jacket",
            "Trapstar decoded jacket",
            "Trapstar shooters",
            "Central Cee jacket",
            "Central Cee photoshoot",
            "Central Cee style",
            "Central Cee wallpaper",
            "Central Cee street style",
            "Trapstar reflective"
        ]
        
        for q in test_queries:
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
                return res.slice(0, 3);
            }''')
            print(f"=== {q} ===")
            for it in items:
                print(f"  {it['title'][:40]} -> {it['url']}")
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_bing_queries())
