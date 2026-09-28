import asyncio
import json
from playwright.async_api import async_playwright

async def find_verified_images():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        queries = [
            ('site:grailed.com Trapstar Decoded Puffer', 'trapstar_puffer'),
            ('site:grailed.com Trapstar Shooters Tracksuit', 'trapstar_tracksuit'),
            ('site:thefashionisto.com Central Cee', 'central_cee_fashion'),
            ('site:pausemag.co.uk Central Cee', 'central_cee_pause'),
            ('site:pinterest.com Central Cee Trapstar', 'central_cee_trapstar_pin'),
            ('site:grailed.com Trapstar Decoded 2.0 Puffer 3M', 'trapstar_3m_puffer')
        ]
        
        for q, label in queries:
            url = f'https://www.bing.com/images/search?q={q}'
            await page.goto(url)
            await page.wait_for_timeout(2500)
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
                return res.slice(0, 5);
            }''')
            print(f'=== Results for {label} ===')
            for item in items:
                print(item['title'], '->', item['url'])
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(find_verified_images())
